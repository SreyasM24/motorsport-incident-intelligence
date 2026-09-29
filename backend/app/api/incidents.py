"""API router for incidents and evidence dossiers."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.core.logging import logger
from app.database.connection import get_db
from app.evidence.dossier import convert_dossier_to_frontend_incident
from app.evidence.reconstruction_service import get_reconstruction_engine
from app.evidence.cv import get_cv_service
from app.evidence.synthesis import (
    DossierExportPayload,
    StewardEvidenceDossier,
    get_steward_dossier_synthesizer,
)
from app.evidence.regulation_evidence import match_relevant_regulations
from app.models.incident import Incident
from app.models.incident_driver import IncidentDriver
from app.schemas.incident import (
    EvidenceItemSchema,
    EvidenceRegulationConnectionSchema,
    EvidenceSources,
    IncidentDetailResponse,
    IncidentStatusUpdate,
    IncidentSummary,
    IncidentTimelineMilestoneSchema,
    TimeWindow,
)
from app.schemas.regulation import RelevantRegulationSchema
from app.schemas.review import (
    ReviewCreateRequest,
    ReviewRecordSchema,
    ReviewStatus,
)
from app.services.candidate_persistence_service import CandidatePersistenceService
from app.services.dossier_cache_service import get_dossier_cache

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentSummary], summary="List incident candidates")
def get_incidents(
    race_id: Optional[str] = Query(default=None, description="Filter by race event ID"),
    session_id: Optional[str] = Query(default=None, description="Filter by session ID"),
    driver: Optional[str] = Query(default=None, description="Filter by involved driver code, e.g. VER"),
    status: Optional[str] = Query(default=None, description="Filter by review status"),
    severity: Optional[str] = Query(default=None, description="Filter by severity rating"),
    min_confidence: Optional[int] = Query(default=0, ge=0, le=100, description="Minimum evidence strength score"),
    search: Optional[str] = Query(default=None, description="Search term for turn, description, or drivers"),
    auto_seed: bool = Query(default=False, description="Auto-seed reference Monza incidents if table is empty"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results returned"),
    db: Session = Depends(get_db),
) -> List[IncidentSummary]:
    """Retrieve all candidate incidents matching filter parameters."""
    stmt = select(Incident)

    if session_id:
        stmt = stmt.where(Incident.session_id == session_id)
    if status and status != "ALL":
        stmt = stmt.where(Incident.status == status)
    if severity and severity != "ALL":
        stmt = stmt.where(Incident.severity == severity)
    if min_confidence:
        stmt = stmt.where(Incident.evidence_strength >= min_confidence)
    if search:
        search_fmt = f"%{search.lower()}%"
        stmt = stmt.where(
            Incident.id.ilike(search_fmt)
            | Incident.turn.ilike(search_fmt)
            | Incident.incident_type.ilike(search_fmt)
            | Incident.summary.ilike(search_fmt)
        )

    stmt = stmt.order_by(Incident.lap.asc(), Incident.timestamp_str.asc()).limit(limit)
    incidents = db.scalars(stmt).all()

    if auto_seed and not incidents and not search and (not status or status == "ALL"):
        try:
            for ref_id in ("REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"):
                CandidatePersistenceService.persist_by_candidate_id(db, ref_id)
            incidents = db.scalars(stmt).all()
        except Exception as e:
            logger.info(f"Auto-persistence notice: {e}")

    results: List[IncidentSummary] = []
    for inc in incidents:
        # Determine involved driver codes
        drivers = [p.driver.code for p in inc.drivers_involved if p.driver]
        driver_a = drivers[0] if len(drivers) > 0 else "CAR A"
        driver_b = drivers[1] if len(drivers) > 1 else "CAR B"

        if driver and driver.upper() not in [d.upper() for d in drivers]:
            continue

        circuit_name = inc.session.race.circuit if inc.session and inc.session.race else "Circuit"
        session_name = inc.session.name if inc.session else "Race"

        results.append(
            IncidentSummary(
                id=inc.id,
                session=f"{circuit_name} — {session_name}",
                race_id=inc.session.race_id if inc.session else "",
                circuit=circuit_name,
                lap=inc.lap,
                turn=inc.turn,
                timestamp=inc.timestamp_str,
                driver_a=driver_a,
                driver_b=driver_b,
                incident_type=inc.incident_type,
                confidence=inc.evidence_strength,
                status=inc.status,
                severity=inc.severity,
            )
        )

    return results


@router.get("/{incident_id}", response_model=IncidentDetailResponse, summary="Get full incident evidence dossier")
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
) -> IncidentDetailResponse:
    """Retrieve complete multi-source evidence dossier for an incident."""
    inc = db.get(Incident, incident_id)
    if not inc:
        # Fallback: check if incident_id is a reconstructed candidate or reference case
        engine = get_reconstruction_engine()
        dossier = engine.get_candidate_dossier(incident_id)
        if dossier:
            return convert_dossier_to_frontend_incident(dossier)
        raise ResourceNotFoundException("Incident", incident_id)

    drivers = [p.driver.code for p in inc.drivers_involved if p.driver]
    driver_a = drivers[0] if len(drivers) > 0 else "CAR A"
    driver_b = drivers[1] if len(drivers) > 1 else "CAR B"

    circuit_name = inc.session.race.circuit if inc.session and inc.session.race else "Circuit"
    session_name = inc.session.name if inc.session else "Race"

    # Match statutory regulations and evidence-regulation connections
    reg_summary = match_relevant_regulations(
        event_type=inc.incident_type,
        minimum_gap=1.82,
        decel_delta_g=1.5,
    )
    frontend_regs = [
        RelevantRegulationSchema(
            id=r.id,
            document=r.document,
            article=r.article,
            title=r.title,
            regulation_text_placeholder=r.text_reference,
            why_relevant=r.relevance_reason,
            match_reason="Algorithmic match based on empirical interaction kinematics.",
            relevance=r.relevance_level,
            source=r.series,
            source_url=r.source_url,
        )
        for r in reg_summary.references
    ]
    frontend_connections = [
        EvidenceRegulationConnectionSchema(
            observed_evidence=link.observed_evidence,
            relevant_regulation=link.relevant_regulation,
            steward_review_action=link.steward_review_action,
        )
        for link in reg_summary.evidence_links
    ]

    return IncidentDetailResponse(
        id=inc.id,
        session=f"{circuit_name} — {session_name}",
        race_id=inc.session.race_id if inc.session else "",
        circuit=circuit_name,
        lap=inc.lap,
        turn=inc.turn,
        timestamp=inc.timestamp_str,
        time_window=TimeWindow(
            start=inc.start_time.strftime("%H:%M:%S.%f")[:-5] if inc.start_time else inc.timestamp_str,
            end=inc.end_time.strftime("%H:%M:%S.%f")[:-5] if inc.end_time else inc.timestamp_str,
        ),
        driver_a=driver_a,
        driver_b=driver_b,
        incident_type=inc.incident_type,
        confidence=inc.evidence_strength,
        status=inc.status,
        severity=inc.severity,
        summary=inc.summary or "Algorithmic telemetry interaction candidate flagged for steward review.",
        detection_method=inc.detection_method or "Multi-channel relative motion telemetry anomaly",
        video_available=inc.video_available,
        video_path=inc.video_path,
        telemetry_available=inc.telemetry_available,
        regulations_available=len(frontend_regs) > 0,
        sources=EvidenceSources(),
        evidence_assessment=[],
        relevant_regulations=frontend_regs,
        evidence_connections=frontend_connections,
        timeline=[],
        uncertainties=[
            "Telemetry traces reflect mechanical and sensor physics; they do NOT measure driver psychological intent.",
            "Visual onboard feed undergoing sub-millisecond sync calibration with ECU clock.",
            "This platform produces deterministic evidence reconstruction; it never issues penalties or verdicts.",
            "Final sporting adjudication strictly requires deliberation by appointed FIA Human Race Stewards.",
        ],
    )


@router.patch("/{incident_id}/status", response_model=IncidentSummary, summary="Update human steward review status")
def update_incident_status(
    incident_id: str,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
) -> IncidentSummary:
    """Update steward workflow status with strict state machine transition validation."""
    inc = db.get(Incident, incident_id)
    if not inc:
        raise ResourceNotFoundException("Incident", incident_id)

    review_req = ReviewCreateRequest(
        status=payload.status,
        reviewer_id=payload.reviewer_id or "steward-panel",
        review_notes=payload.review_notes,
        review_rationale=payload.review_rationale,
        reopen_reason=payload.reopen_reason,
    )

    inc, _ = CandidatePersistenceService.transition_status(db, incident_id, review_req)

    drivers = [p.driver.code for p in inc.drivers_involved if p.driver]
    driver_a = drivers[0] if len(drivers) > 0 else "CAR A"
    driver_b = drivers[1] if len(drivers) > 1 else "CAR B"
    circuit_name = inc.session.race.circuit if inc.session and inc.session.race else "Circuit"

    return IncidentSummary(
        id=inc.id,
        session=f"{circuit_name} — Race",
        race_id=inc.session.race_id if inc.session else "",
        circuit=circuit_name,
        lap=inc.lap,
        turn=inc.turn,
        timestamp=inc.timestamp_str,
        driver_a=driver_a,
        driver_b=driver_b,
        incident_type=inc.incident_type,
        confidence=inc.evidence_strength,
        status=inc.status,
        severity=inc.severity,
    )


@router.get("/{incident_id}/reviews", response_model=List[ReviewRecordSchema], summary="Get incident review audit history")
def get_incident_reviews_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
) -> List[ReviewRecordSchema]:
    """Retrieve complete chronological human steward review log for an incident."""
    inc = db.get(Incident, incident_id)
    if not inc:
        raise ResourceNotFoundException("Incident", incident_id)

    reviews = CandidatePersistenceService.get_incident_reviews(db, incident_id)
    return [
        ReviewRecordSchema(
            id=r.id,
            incident_id=r.incident_id,
            status=ReviewStatus(r.status),
            reviewer_id=r.reviewer_id,
            review_started_at=r.review_started_at,
            review_completed_at=r.review_completed_at,
            evidence_considered=r.evidence_considered,
            evidence_missing=r.evidence_missing,
            observations=r.observations,
            review_notes=r.review_notes,
            review_rationale=r.review_rationale,
            regulatory_references=r.regulatory_references,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in reviews
    ]


@router.post("/{incident_id}/reviews", response_model=ReviewRecordSchema, summary="Submit steward review notes and status update")
def create_incident_review_endpoint(
    incident_id: str,
    payload: ReviewCreateRequest,
    db: Session = Depends(get_db),
) -> ReviewRecordSchema:
    """Submit a formal human steward review entry (notes, observations, determination)."""
    inc, review = CandidatePersistenceService.transition_status(db, incident_id, payload)
    return ReviewRecordSchema(
        id=review.id,
        incident_id=review.incident_id,
        status=ReviewStatus(review.status),
        reviewer_id=review.reviewer_id,
        review_started_at=review.review_started_at,
        review_completed_at=review.review_completed_at,
        evidence_considered=review.evidence_considered,
        evidence_missing=review.evidence_missing,
        observations=review.observations,
        review_notes=review.review_notes,
        review_rationale=review.review_rationale,
        regulatory_references=review.regulatory_references,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.get(
    "/{incident_id}/dossier",
    response_model=StewardEvidenceDossier,
    summary="Retrieve canonical multi-modal Steward Evidence Dossier for an incident",
)
def get_incident_steward_dossier_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
) -> StewardEvidenceDossier:
    """Retrieve canonical Steward Evidence Dossier integrating review state and multi-modal streams."""
    inc = db.get(Incident, incident_id)
    cand_lookup = inc.candidate_id if inc and inc.candidate_id else incident_id
    
    # 1. Check cache for pre-synthesized mathematical evidence snapshot
    cache = get_dossier_cache()
    analysis_ver = getattr(inc, "analysis_version", "v1.0") or "v1.0"
    prep_ver = getattr(inc, "preprocessing_version", "v1") or "v1"
    cache_key = cache.build_cache_key(candidate_id=cand_lookup, analysis_version=analysis_ver, preprocessing_version=prep_ver)
    
    cached_dossier = cache.get_snapshot(cache_key)
    reviews = CandidatePersistenceService.get_incident_reviews(db, incident_id)
    review_record = reviews[-1].__dict__ if reviews else {}
    if inc:
        review_record["status"] = inc.status

    if cached_dossier:
        # Separate concerns: inject latest mutable review state into immutable evidence snapshot
        return cache.inject_live_review_state(cached_dossier, review_record)


    # 2. Cache miss: perform multi-modal synthesis
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(cand_lookup)
    if not dossier:
        raise ResourceNotFoundException("Incident", incident_id)

    cv_analysis = get_cv_service().process_candidate_incident(candidate=dossier.candidate)

    synthesized_dossier = get_steward_dossier_synthesizer().synthesize_steward_dossier(
        dossier=dossier,
        cv_analysis=cv_analysis,
        review_record=review_record,
    )
    
    # Store snapshot in cache
    cache.set_snapshot(cache_key, synthesized_dossier, candidate_id=cand_lookup)
    return synthesized_dossier



@router.get(
    "/{incident_id}/dossier/export/json",
    response_model=DossierExportPayload,
    summary="Export deterministic machine-readable Steward Evidence Dossier JSON for an incident",
)
@router.get(
    "/{incident_id}/dossier/json",
    response_model=DossierExportPayload,
    include_in_schema=False,
)
def export_incident_steward_dossier_json_endpoint(
    incident_id: str,
    db: Session = Depends(get_db),
) -> DossierExportPayload:
    """Export machine-readable JSON dossier payload for an incident."""
    steward_dossier = get_incident_steward_dossier_endpoint(incident_id, db)
    return get_steward_dossier_synthesizer().export_dossier_json(steward_dossier)


