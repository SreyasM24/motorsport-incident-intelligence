from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.evidence.baseline_models import BaselineEvidence
from app.schemas.overtake_geometry import OvertakeGeometryEvidence
from app.schemas.ml_evidence import MLEvidence, BenchmarkEvaluationResponse
from app.evidence.video_evidence import VideoEvidenceSummary
from app.evidence.visual import VisualEvidenceSummary
from app.evidence.cv import CVIncidentAnalysisResponse, get_cv_service
from app.evidence.cv.eval import (
    CVEvaluationSuiteResponse,
    IncidentVisualEvidenceSufficiency,
    VideoDatasetCatalog,
    get_cv_evaluation_service,
)
from app.evidence.synthesis import (
    DossierExportPayload,
    StewardEvidenceDossier,
    get_steward_dossier_synthesizer,
)
from app.ml.evaluation import BenchmarkEvaluationReport
from app.evidence.candidate import (
    CandidateBatchResponse,
    CandidateDossier,
    CandidateQueryRequest,
)
from app.evidence.dossier import (
    IncidentEvidenceDossier,
    convert_dossier_to_frontend_incident,
)
from app.evidence.evaluation import (
    MONZA_2024_REFERENCE_CASES,
    EvaluationMetrics,
    evaluate_candidates_against_ground_truth,
)
from app.evidence.reconstruction_service import get_reconstruction_engine
from app.schemas.incident import IncidentDetailResponse
from app.schemas.review import (
    BulkCandidatePersistRequest,
    BulkCandidatePersistResponse,
    CandidatePersistRequest,
    CandidatePersistResponse,
)
from app.services.candidate_persistence_service import CandidatePersistenceService
from app.benchmark import (
    BenchmarkSuiteReport,
    CaseEvaluationReport,
    ComparableIncidentMatch,
    ComparatorEvaluationReport,
    MetricProvenanceAudit,
    get_benchmark_service,
)

router = APIRouter(prefix="/analysis", tags=["Analysis & Candidate Reconstruction"])


@router.post(
    "/candidates/persist",
    response_model=CandidatePersistResponse,
    summary="Persist a reconstructed candidate into the reviewable Incident table (Idempotent)",
)
def persist_candidate_endpoint(
    request: CandidatePersistRequest,
    db: Session = Depends(get_db),
) -> CandidatePersistResponse:
    """Persist an algorithmic candidate event into the database for human steward review.

    Guarantees idempotency via deterministic canonical fingerprinting.
    """
    try:
        return CandidatePersistenceService.persist_by_candidate_id(
            db=db,
            candidate_id=request.candidate_id,
            session_id=request.session_id,
            reviewer_id=request.reviewer_id,
            notes=request.initial_notes,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Candidate persistence failed: {str(e)}",
        )


@router.post(
    "/candidates/persist-batch",
    response_model=BulkCandidatePersistResponse,
    summary="Bounded bulk candidate reconstruction and persistence",
)
def persist_bulk_candidates_endpoint(
    request: BulkCandidatePersistRequest,
    db: Session = Depends(get_db),
) -> BulkCandidatePersistResponse:
    """Execute bounded candidate detection and persist results into review table."""
    try:
        return CandidatePersistenceService.persist_bulk_candidates(db=db, request=request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk candidate persistence failed: {str(e)}",
        )



@router.post(
    "/candidates",
    response_model=CandidateBatchResponse,
    summary="Reconstruct candidate events across bounded driver pairs or scope",
)
def reconstruct_candidates(
    request: CandidateQueryRequest,
) -> CandidateBatchResponse:
    """Execute bounded incident candidate detection and event segmentation.

    CRITICAL DOCTRINE:
        This endpoint extracts empirical interaction candidates requiring further
        steward review. It does NOT decide guilt, fault, or penalties.
    """
    try:
        engine = get_reconstruction_engine()
        response = engine.analyze_session_scope(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Candidate reconstruction failed: {str(e)}",
        )


@router.get(
    "/candidates/{candidate_id}/dossier",
    response_model=IncidentEvidenceDossier,
    summary="Retrieve unified multi-modal evidence dossier for an incident candidate",
)
def get_candidate_dossier_endpoint(candidate_id: str) -> IncidentEvidenceDossier:
    """Retrieve full multi-modal evidence dossier for a candidate.

    Combines telemetry summary, chronological timeline, race control messages,
    video synchronization metadata, and statutory regulations into a verifiable
    evidence package for human steward investigation.
    """
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    return dossier


@router.get(
    "/candidates/{candidate_id}/baseline",
    response_model=BaselineEvidence,
    summary="Retrieve reference-lap baseline and evidence quantification for candidate",
)
def get_candidate_baseline_endpoint(candidate_id: str) -> BaselineEvidence:
    """Retrieve quantified reference-lap baseline metrics and trajectory deviations."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    if not dossier.baseline_evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline evidence for candidate '{candidate_id}' is unavailable.",
        )
    return dossier.baseline_evidence


@router.get(
    "/candidates/{candidate_id}/overtake-geometry",
    response_model=OvertakeGeometryEvidence,
    summary="Retrieve cornering overtake geometry and apex overlap evidence for candidate",
)
def get_candidate_overtake_geometry_endpoint(candidate_id: str) -> OvertakeGeometryEvidence:
    """Retrieve quantified cornering overtake geometry, apex overlap, and exit clearance metrics."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    if not dossier.overtake_geometry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Overtake geometry evidence for candidate '{candidate_id}' is unavailable.",
        )
    return dossier.overtake_geometry


@router.get(
    "/candidates/{candidate_id}/ml-evaluation",
    response_model=MLEvidence,
    summary="Retrieve machine learning candidate evaluation and feature contributions",
)
def get_candidate_ml_evaluation_endpoint(candidate_id: str) -> MLEvidence:
    """Retrieve non-binding ML candidate anomaly probability and top contributing features."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    if not dossier.ml_evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ML evaluation for candidate '{candidate_id}' is unavailable.",
        )
    return dossier.ml_evidence


@router.get(
    "/candidates/{candidate_id}/video",
    response_model=VideoEvidenceSummary,
    summary="Retrieve multi-camera video evidence, synchronization status, and incident playback windows",
)
def get_candidate_video_evidence_endpoint(candidate_id: str) -> VideoEvidenceSummary:
    """Retrieve video evidence summary, temporal synchronization transforms, and playback windows.
    
    If no verified broadcast or onboard feed is linked, honestly returns VIDEO_UNAVAILABLE
    with transparent provenance and limitations.
    """
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    return dossier.video_evidence


@router.get(
    "/candidates/{candidate_id}/video/synchronization",
    response_model=Dict[str, Any],
    summary="Retrieve detailed mathematical synchronization transform, calibration points, and uncertainty",
)
def get_candidate_video_synchronization_endpoint(candidate_id: str) -> Dict[str, Any]:
    """Retrieve fine-grained temporal calibration parameters, residual errors, and uncertainty bounds."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    vid = dossier.video_evidence
    return {
        "candidateId": candidate_id,
        "syncStatus": vid.video_evidence_status.value,
        "uncertainty": vid.uncertainty.model_dump(by_alias=True) if vid.uncertainty else None,
        "incidentWindow": vid.incident_window.model_dump(by_alias=True) if vid.incident_window else None,
        "multiCamera": [c.model_dump(by_alias=True) for c in vid.multi_camera],
        "cvReadinessFrame": vid.cv_readiness_frame.model_dump(by_alias=True) if vid.cv_readiness_frame else None,
        "statement": vid.statement,
        "limitations": vid.limitations,
    }


@router.get(
    "/candidates/{candidate_id}/video/visual-evidence",
    response_model=VisualEvidenceSummary,
    summary="Retrieve bounded visual evidence, ROIs, keyframes, and cross-modal telemetry alignment",
)
def get_candidate_visual_evidence_endpoint(candidate_id: str) -> VisualEvidenceSummary:
    """Retrieve bounded 2D visual evidence, object tracks, keyframe metrics, and cross-modal alignment."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    if dossier.visual_evidence is not None:
        return dossier.visual_evidence

    from app.evidence.visual import get_visual_evidence_service
    return get_visual_evidence_service().build_visual_evidence_for_candidate(
        candidate_id=dossier.candidate_id,
        session_id=dossier.session_id,
        event_start_str=dossier.candidate.event_start,
        event_peak_str=dossier.candidate.event_peak,
        event_end_str=dossier.candidate.event_end,
        driver_a=dossier.candidate.driver_a,
        driver_b=dossier.candidate.driver_b,
    )


@router.get(
    "/candidates/{candidate_id}/video/cv",
    response_model=CVIncidentAnalysisResponse,
    summary="Retrieve Computer Vision vehicle detection, tracking, track quality, and identity evidence",
)
def get_candidate_cv_analysis_endpoint(candidate_id: str) -> CVIncidentAnalysisResponse:
    """Retrieve Computer Vision vehicle detections, multi-object tracks, quality ratings, and identity associations.
    
    Returns VIDEO_UNAVAILABLE honestly if broadcast video is unlinked or protected under commercial copyright.
    Returns MODEL_UNAVAILABLE honestly if detector weights are not configured.
    """
    clean_cid = (candidate_id or "").upper()
    if clean_cid in {"REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"}:
        return get_cv_service().analyze_incident_window(
            candidate_id=candidate_id,
            session_id="Italian Grand Prix 2024 — Race",
        )

    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    return get_cv_service().process_candidate_incident(candidate=dossier.candidate)


@router.get(
    "/ml/benchmark-evaluation",
    response_model=BenchmarkEvaluationResponse,
    summary="Retrieve benchmark evaluation metrics comparing ML model to deterministic detector",
)
@router.get(
    "/ml/evaluation",
    response_model=BenchmarkEvaluationResponse,
    summary="Retrieve multi-circuit benchmark evaluation metrics and model comparison",
)
def get_ml_benchmark_evaluation_endpoint() -> BenchmarkEvaluationResponse:
    """Retrieve leave-one-group-out cross validation metrics and baseline comparison."""
    report = BenchmarkEvaluationReport()
    data = report.evaluate_leave_one_group_out()
    return BenchmarkEvaluationResponse(**data)


@router.get(
    "/candidates/{candidate_id}/frontend-incident",
    response_model=IncidentDetailResponse,
    summary="Retrieve candidate dossier mapped into the frontend IncidentDetailResponse contract",
)
def get_candidate_frontend_incident_endpoint(
    candidate_id: str,
    circuit: str = Query(default="Monza", description="Circuit name"),
    session: str = Query(default="Italian Grand Prix 2024 — Race", description="Session label"),
) -> IncidentDetailResponse:
    """Retrieve candidate dossier transformed for direct consumption by frontend views."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found.",
        )
    return convert_dossier_to_frontend_incident(dossier, circuit_name=circuit, session_name=session)


@router.get(
    "/reference-cases",
    summary="Retrieve official steward ground truth reference cases for evaluation",
)
def get_reference_cases() -> List[dict]:
    """Retrieve ground-truth reference incident cases for evaluation benchmarks."""
    return [
        {
            "caseId": ref.case_id,
            "sessionId": ref.session_id,
            "season": ref.season,
            "round": ref.round_name,
            "lap": ref.lap,
            "driverA": ref.driver_a,
            "driverB": ref.driver_b,
            "approxTime": ref.approx_time,
            "fiaDocument": ref.fia_document,
            "infringementType": ref.infringement_type,
            "officialFinding": ref.official_finding,
            "description": ref.description,
        }
        for ref in MONZA_2024_REFERENCE_CASES
    ]


@router.get(
    "/cv/dataset",
    response_model=VideoDatasetCatalog,
    summary="Retrieve canonical real video manifest catalog, authorization statuses, and split distributions",
)
def get_cv_dataset_catalog_endpoint() -> VideoDatasetCatalog:
    """Retrieve catalog of real, research, and synthetic video records for CV evaluation.

    Strictly reports real-world video availability and legal authorization statuses.
    UNAUTHORIZED footage is strictly excluded from active evaluation pools.
    """
    return get_cv_evaluation_service().load_real_video_manifest()


@router.get(
    "/cv/evaluation",
    response_model=CVEvaluationSuiteResponse,
    summary="Retrieve system-wide Computer Vision evaluation, dataset manifest discovery, and error analysis",
)
def get_cv_evaluation_endpoint() -> CVEvaluationSuiteResponse:
    """Retrieve system-wide CV benchmark evaluation report, error breakdown, and dataset discovery status.

    Guarantees honest transparency: reports REAL_VIDEO_STATUS = NOT_AVAILABLE and
    SYNTHETIC_VALIDATION_ONLY when official commercial broadcast video is not bundled.
    """
    return get_cv_evaluation_service().get_evaluation_suite()


@router.get(
    "/candidates/{candidate_id}/video/cv/sufficiency",
    response_model=IncidentVisualEvidenceSufficiency,
    summary="Evaluate whether visual evidence for a candidate is sufficient for human steward inspection",
)
def get_candidate_cv_sufficiency_endpoint(candidate_id: str) -> IncidentVisualEvidenceSufficiency:
    """Evaluate whether visual evidence for an incident candidate is sufficient for steward inspection.

    Strictly answers: 'Is there sufficient visual evidence for steward review?'.
    It NEVER answers 'Who caused the incident?' or assigns fault.
    """
    clean_cid = (candidate_id or "").upper()
    if clean_cid in {"REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"}:
        return get_cv_evaluation_service().evaluate_incident_sufficiency(
            candidate_id=candidate_id,
            cv_analysis=None,
        )

    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    cv_analysis = get_cv_service().process_candidate_incident(candidate=dossier.candidate)
    return get_cv_evaluation_service().evaluate_incident_sufficiency(
        candidate_id=candidate_id,
        cv_analysis=cv_analysis,
    )


@router.get(
    "/candidates/{candidate_id}/steward-dossier",
    response_model=StewardEvidenceDossier,
    summary="Retrieve canonical multi-modal Steward Evidence Dossier with discrepancy analysis",
)
def get_candidate_steward_dossier_endpoint(candidate_id: str) -> StewardEvidenceDossier:
    """Retrieve unified, discrepancy-aware Steward Evidence Dossier across all 8 evidence streams."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(candidate_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate dossier for '{candidate_id}' not found.",
        )
    cv_analysis = get_cv_service().process_candidate_incident(candidate=dossier.candidate)
    return get_steward_dossier_synthesizer().synthesize_steward_dossier(
        dossier=dossier,
        cv_analysis=cv_analysis,
        candidate_id_override=candidate_id,
    )


@router.get(
    "/candidates/{candidate_id}/dossier/export/json",
    response_model=DossierExportPayload,
    summary="Export deterministic machine-readable Steward Evidence Dossier JSON",
)
@router.get(
    "/candidates/{candidate_id}/steward-dossier/export/json",
    response_model=DossierExportPayload,
    include_in_schema=False,
)
def export_candidate_steward_dossier_json_endpoint(candidate_id: str) -> DossierExportPayload:
    """Export machine-readable JSON dossier payload for external steward panels or FIA compliance."""
    steward_dossier = get_candidate_steward_dossier_endpoint(candidate_id)
    return get_steward_dossier_synthesizer().export_dossier_json(steward_dossier)


# ==============================================================================
# HISTORICAL INCIDENT RECONSTRUCTION BENCHMARK ENDPOINTS (PROMPT 19)
# ==============================================================================

@router.get(
    "/benchmark/historical-incidents",
    response_model=BenchmarkSuiteReport,
    summary="Execute and retrieve the Historical Incident Reconstruction Benchmark Suite Report",
)
def get_historical_incident_benchmark_report_endpoint(
    force_refresh: bool = Query(False, description="Re-run evaluation suite bypassing cache"),
) -> BenchmarkSuiteReport:
    """Execute multidimensional evidence quality evaluation over authoritative historical F1 incidents.

    STRICT NON-ADJUDICATIVE PHILOSOPHY:
        Evaluates evidence reconstruction quality only. Does not predict driver guilt,
        assign fault, or recommend sporting penalties.
    """
    service = get_benchmark_service()
    return service.run_benchmark_suite(force_refresh=force_refresh)


@router.get(
    "/benchmark/historical-incidents/{case_id}",
    response_model=CaseEvaluationReport,
    summary="Retrieve detailed evidence reconstruction evaluation for a specific historical benchmark case",
)
def get_historical_incident_case_evaluation_endpoint(case_id: str) -> CaseEvaluationReport:
    """Retrieve fine-grained timestamp, vehicle, kinematic, regulatory, and epistemic evaluation for a case."""
    service = get_benchmark_service()
    report = service.evaluate_single_case(case_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Historical benchmark case '{case_id}' not found.",
        )
    return report


@router.get(
    "/benchmark/historical-incidents/{case_id}/comparable",
    response_model=List[ComparableIncidentMatch],
    summary="Retrieve observable historically comparable incidents based on physical geometry",
)
def get_comparable_historical_incidents_endpoint(
    case_id: str,
    top_k: int = Query(3, ge=1, le=10, description="Maximum number of comparable cases to return"),
) -> List[ComparableIncidentMatch]:
    """Retrieve comparable incidents based strictly on observable kinematics and track geometry.

    STRICT COMPLIANCE GUARDRAIL:
        Past steward decisions are displayed strictly as documentary context.
        Prior outcomes do NOT determine current guilt or penalty recommendations.
    """
    service = get_benchmark_service()
    matches = service.find_comparable_cases(case_id=case_id, top_k=top_k)
    return matches


@router.get(
    "/benchmark/provenance-matrix",
    response_model=List[MetricProvenanceAudit],
    summary="Retrieve the authoritative Ground Truth vs System Independence Audit Matrix",
)
def get_benchmark_provenance_matrix_endpoint() -> List[MetricProvenanceAudit]:
    """Retrieve fine-grained provenance audit distinguishing independent vs telemetry-consistency metrics.

    CRITICAL SCIENTIFIC INTEGRITY (PROMPT 20):
        Identifies whether ground truth and system sources share underlying computational pathways
        to prevent circular evaluation.
    """
    service = get_benchmark_service()
    return service.get_provenance_matrix()


@router.get(
    "/benchmark/splits",
    response_model=Dict[str, Any],
    summary="Retrieve leakage-free group-aware cross-validation splits (LOCO / LOSO / LOEO)",
)
def get_benchmark_group_splits_endpoint(
    split_type: str = Query("circuit", description="Grouping dimension: 'circuit', 'season', or 'event'"),
) -> Dict[str, Any]:
    """Retrieve Leave-One-Circuit-Out, Leave-One-Season-Out, or Leave-One-Event-Out partitions."""
    service = get_benchmark_service()
    return service.get_group_splits(split_type=split_type)


@router.get(
    "/benchmark/comparator-evaluation",
    response_model=ComparatorEvaluationReport,
    summary="Retrieve evaluation report for historical comparable incident engine",
)
def get_comparator_evaluation_endpoint(
    top_k: int = Query(3, ge=1, le=10, description="Top-k matches to evaluate"),
) -> ComparatorEvaluationReport:
    """Evaluate observable physical similarity and assert zero precedent/penalty leakage."""
    service = get_benchmark_service()
    return service.evaluate_comparator(top_k=top_k)





