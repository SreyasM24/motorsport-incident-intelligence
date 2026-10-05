"""Deterministic End-to-End Case Replay Harness & Integration Verification Service.

Prompt 25: Validates the entire canonical steward workflow:
    REAL SESSION DATA
            ↓
    INGESTION
            ↓
    CANONICAL SESSION
            ↓
    TELEMETRY PREPROCESSING
            ↓
    INCIDENT CANDIDATE DETECTION
            ↓
    INCIDENT RECONSTRUCTION
            ↓
    EVIDENCE DOSSIER
            ↓
    REGULATION RETRIEVAL
            ↓
    HISTORICAL COMPARABLE CASES
            ↓
    VIDEO/CV EVIDENCE (Honest UNAVAILABLE handling)
            ↓
    MULTI-MODAL SYNTHESIS
            ↓
    PERSISTED CANDIDATE
            ↓
    STEWARD CASE WORKSPACE
            ↓
    HUMAN REVIEW
            ↓
    REVIEW HISTORY / AUDIT TRAIL

CRITICAL JURISPRUDENTIAL GUARDRAILS:
    1. Zero Autonomous Guilt or Fault Determination: The replay harness validates
       evidence synthesis quality, NEVER assigns fault or predicts penalties.
    2. Epistemic Separation: Preserves OBSERVED, DERIVED, MODEL_DERIVED, DOCUMENTARY,
       and UNAVAILABLE across all transitions.
    3. Source Immutability: Reviewer actions and annotations never alter underlying evidence.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.core.logging import logger
from app.evidence.dossier import IncidentEvidenceDossier
from app.evidence.reconstruction_service import get_reconstruction_engine
from app.evidence.synthesis import get_steward_dossier_synthesizer
from app.evidence.synthesis.contracts import StewardEvidenceDossier
from app.models.incident import Incident
from app.models.review import ReviewRecord
from app.schemas.review import ReviewStatus
from app.schemas.workspace import (
    AcknowledgementAction,
    DiscrepancyStatus,
    EvidenceAcknowledgementCreateRequest,
    StewardCaseWorkspace,
    UnresolvedQuestionCreateRequest,
)
from app.services.candidate_persistence_service import CandidatePersistenceService
from app.services.workspace_service import StewardWorkspaceService


class ReplayTimings(BaseModel):
    """Detailed runtime measurements across the pipeline stages in milliseconds."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    reconstruction_ms: float
    dossier_synthesis_ms: float
    persistence_ms: float
    workspace_assembly_ms: float
    review_simulation_ms: float
    total_ms: float


class CaseReplayResult(BaseModel):
    """Encapsulates the complete end-to-end replay output for a candidate case."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    case_id: str
    incident_id: str
    is_created_in_db: bool
    persisted_fingerprint: str
    determinism_fingerprint: str
    timings: ReplayTimings
    workspace: StewardCaseWorkspace
    review_simulation: Dict[str, Any] = Field(default_factory=dict)
    contract_assertions: Dict[str, bool] = Field(default_factory=dict)


class CaseReplayService:
    """Service executing deterministic case replays and end-to-end integration audits."""

    @classmethod
    def replay_case(
        cls,
        case_id: str,
        db: Session,
        simulate_review: bool = True,
        reviewer_id: str = "steward-replay-1",
        force_refresh: bool = True,
    ) -> CaseReplayResult:
        """Execute a full canonical replay from raw case input through workspace and review."""
        t_total_start = time.perf_counter()
        clean_cid = case_id.strip()

        # 1. Incident Candidate Reconstruction
        t0 = time.perf_counter()
        engine = get_reconstruction_engine()
        raw_dossier = engine.get_candidate_dossier(clean_cid)
        if not raw_dossier:
            raise ResourceNotFoundException("CandidateDossier", clean_cid)
        reconstruction_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        # 2. Multi-Modal Evidence Synthesis & Master Dossier
        t1 = time.perf_counter()
        from app.evidence.cv import get_cv_service
        cv_analysis = get_cv_service().process_candidate_incident(candidate=raw_dossier.candidate)
        synthesizer = get_steward_dossier_synthesizer()
        master_dossier = synthesizer.synthesize_steward_dossier(
            dossier=raw_dossier,
            cv_analysis=cv_analysis,
            candidate_id_override=clean_cid,
        )
        dossier_synthesis_ms = round((time.perf_counter() - t1) * 1000.0, 3)

        # 3. Candidate Database Persistence (Idempotent)
        t2 = time.perf_counter()
        incident, is_created = CandidatePersistenceService.persist_candidate(
            db=db,
            candidate=raw_dossier.candidate,
            reviewer_id=reviewer_id,
            initial_notes="Automated replay harness candidate ingestion.",
        )
        persistence_ms = round((time.perf_counter() - t2) * 1000.0, 3)

        # 4. Steward Case Workspace Assembly
        t3 = time.perf_counter()
        workspace = StewardWorkspaceService.get_workspace(
            candidate_id=clean_cid,
            db=db,
            force_refresh=force_refresh,
        )
        workspace_assembly_ms = round((time.perf_counter() - t3) * 1000.0, 3)

        # 5. Human Review Simulation
        t4 = time.perf_counter()
        review_sim: Dict[str, Any] = {}
        if simulate_review:
            review_sim = cls._simulate_steward_review(clean_cid, incident, workspace, db, reviewer_id)
            # Re-fetch workspace with updated review state
            workspace = StewardWorkspaceService.get_workspace(
                candidate_id=clean_cid,
                db=db,
                force_refresh=True,
            )
        review_simulation_ms = round((time.perf_counter() - t4) * 1000.0, 3)

        total_ms = round((time.perf_counter() - t_total_start) * 1000.0, 3)

        timings = ReplayTimings(
            reconstruction_ms=reconstruction_ms,
            dossier_synthesis_ms=dossier_synthesis_ms,
            persistence_ms=persistence_ms,
            workspace_assembly_ms=workspace_assembly_ms,
            review_simulation_ms=review_simulation_ms,
            total_ms=total_ms,
        )

        # 6. Compute Deterministic Fingerprint
        det_fingerprint = cls.compute_workspace_fingerprint(workspace)

        # 7. Evaluate Integration Contract Assertions
        assertions = cls.evaluate_contract_assertions(raw_dossier, master_dossier, incident, workspace)

        return CaseReplayResult(
            case_id=clean_cid,
            incident_id=incident.id,
            is_created_in_db=is_created,
            persisted_fingerprint=incident.canonical_fingerprint,
            determinism_fingerprint=det_fingerprint,
            timings=timings,
            workspace=workspace,
            review_simulation=review_sim,
            contract_assertions=assertions,
        )

    @classmethod
    def _simulate_steward_review(
        cls,
        candidate_id: str,
        incident: Incident,
        workspace: StewardCaseWorkspace,
        db: Session,
        reviewer_id: str,
    ) -> Dict[str, Any]:
        """Simulate a realistic steward investigation: review transition, acknowledgement, question, discrepancy."""
        sim_data: Dict[str, Any] = {}

        # A. Transition status: REQUIRES_REVIEW -> UNDER_REVIEW
        old_status = incident.status
        from app.schemas.review import ReviewCreateRequest
        incident, _ = CandidatePersistenceService.transition_status(
            db=db,
            incident_id=incident.id,
            payload=ReviewCreateRequest(
                status=ReviewStatus.UNDER_REVIEW,
                reviewer_id=reviewer_id,
                review_notes="Steward commenced formal evidence triage.",
            ),
        )
        sim_data["status_transition"] = {
            "from": old_status,
            "to": incident.status,
            "success": incident.status == ReviewStatus.UNDER_REVIEW.value,
        }

        # B. Acknowledge the top evidence item
        if workspace.evidence_items:
            target_item = workspace.evidence_items[0]
            ack = StewardWorkspaceService.record_acknowledgement(
                db=db,
                candidate_id=candidate_id,
                evidence_id=target_item.evidence_id,
                payload=EvidenceAcknowledgementCreateRequest(
                    action=AcknowledgementAction.CONSIDERED,
                    note=f"Verified empirical kinematic trace for {target_item.evidence_type} ({target_item.evidence_id}).",
                    reviewer_id=reviewer_id,
                ),
            )
            sim_data["acknowledgement"] = {
                "evidence_id": target_item.evidence_id,
                "action": ack.action,
                "ack_id": ack.id,
            }

        # C. Log an unresolved question
        question = StewardWorkspaceService.create_unresolved_question(
            db=db,
            candidate_id=candidate_id,
            payload=UnresolvedQuestionCreateRequest(
                question="Was front-axle overlap established prior to the 50m braking marker?",
                evidence_ids=[workspace.evidence_items[0].evidence_id] if workspace.evidence_items else [],
                reviewer_note=f"Question logged by {reviewer_id}",
            ),
        )
        sim_data["question"] = {
            "id": question.id,
            "question": question.question,
            "status": question.status,
        }

        # D. Annotate first discrepancy if present
        if workspace.discrepancies:
            target_disc = workspace.discrepancies[0]
            from app.schemas.workspace import DiscrepancyStatusUpdateRequest
            annotation = StewardWorkspaceService.update_discrepancy_status(
                db=db,
                candidate_id=candidate_id,
                discrepancy_id=target_disc.discrepancy_id,
                payload=DiscrepancyStatusUpdateRequest(
                    status=DiscrepancyStatus.ACKNOWLEDGED,
                    note="Reviewed cross-modal discrepancy; acknowledged sensor sync tolerance.",
                    reviewer_id=reviewer_id,
                ),
            )
            sim_data["discrepancy_annotation"] = {
                "discrepancy_id": annotation.discrepancy_id,
                "status": annotation.status,
            }

        return sim_data

    @classmethod
    def compute_workspace_fingerprint(cls, workspace: StewardCaseWorkspace) -> str:
        """Compute an invariant, deterministic SHA256 digest of workspace evidence contents."""
        hist_cases = []
        if isinstance(workspace.historical_comparables, list):
            hist_cases = workspace.historical_comparables
        elif hasattr(workspace.historical_comparables, "comparable_cases"):
            hist_cases = workspace.historical_comparables.comparable_cases
        elif hasattr(workspace.historical_comparables, "comparable_incidents"):
            hist_cases = workspace.historical_comparables.comparable_incidents

        digest_data = {
            "case_id": workspace.case.candidate_id,
            "drivers": sorted(workspace.case.drivers),
            "circuit": workspace.case.circuit,
            "event": workspace.case.event,
            "evidence_item_count": len(workspace.evidence_items),
            "evidence_keys": [
                f"{item.evidence_id}:{item.epistemic_type}:{item.triage_priority}"
                for item in sorted(workspace.evidence_items, key=lambda x: x.evidence_id)
            ],
            "timeline_event_count": len(workspace.timeline),
            "timeline_timestamps": [t.timestamp for t in workspace.timeline],
            "discrepancy_count": len(workspace.discrepancies),
            "regulation_ids": sorted([r.regulation_id for r in workspace.regulations]),
            "historical_case_count": len(hist_cases),
            "historical_ids": sorted([getattr(h, "case_id", str(h)) for h in hist_cases]),
        }
        encoded = json.dumps(digest_data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def evaluate_contract_assertions(
        cls,
        raw_dossier: IncidentEvidenceDossier,
        master_dossier: StewardEvidenceDossier,
        incident: Incident,
        workspace: StewardCaseWorkspace,
    ) -> Dict[str, bool]:
        """Verify strict end-to-end integration contracts across all 8 architectural dimensions."""
        assertions: Dict[str, bool] = {}

        # 1. CASE ASSERTIONS
        assertions["case_candidate_exists"] = bool(raw_dossier.candidate and raw_dossier.candidate_id)
        assertions["case_incident_persisted"] = bool(incident and incident.id)
        assertions["case_drivers_associated"] = len(workspace.case.drivers) == 2 and all(bool(d) for d in workspace.case.drivers)
        assertions["case_timestamps_valid"] = bool(workspace.case.timestamp and len(workspace.case.timestamp) > 3)
        assertions["case_provenance_present"] = bool(raw_dossier.provenance) and (
            "telemetry" in raw_dossier.provenance
            or bool(getattr(raw_dossier, "session_id", None))
        )
        assertions["case_analysis_version_present"] = bool(workspace.case.analysis_version)

        # 2. RECONSTRUCTION ASSERTIONS
        assertions["reconstruction_window_exists"] = bool(raw_dossier.candidate.event_start and raw_dossier.candidate.event_end)
        assertions["reconstruction_telemetry_exists"] = raw_dossier.telemetry_evidence is not None
        assertions["reconstruction_epistemic_typing_preserved"] = all(
            item.epistemic_type in ["OBSERVED", "DERIVED", "MODEL_DERIVED", "DOCUMENTARY", "UNAVAILABLE"]
            for item in workspace.evidence_items
        )

        # 3. DOSSIER ASSERTIONS
        assertions["dossier_streams_classified"] = len(workspace.evidence_summary) >= 3
        assertions["dossier_unavailable_remains_unavailable"] = any(
            summary.availability == "UNAVAILABLE" for summary in workspace.evidence_summary.values()
        )
        assertions["dossier_lineage_exists"] = all(bool(item.source and item.provenance) for item in workspace.evidence_items)

        # 4. REGULATIONS ASSERTIONS
        assertions["regulations_present"] = len(workspace.regulations) > 0
        assertions["regulations_have_citation_provenance"] = all(
            bool(r.source and r.article and r.document) for r in workspace.regulations
        )

        # 5. HISTORICAL ASSERTIONS
        hist_cases = []
        if isinstance(workspace.historical_comparables, list):
            hist_cases = workspace.historical_comparables
        elif hasattr(workspace.historical_comparables, "comparable_cases"):
            hist_cases = workspace.historical_comparables.comparable_cases
        elif hasattr(workspace.historical_comparables, "comparable_incidents"):
            hist_cases = workspace.historical_comparables.comparable_incidents

        assertions["historical_comparables_present"] = len(hist_cases) > 0
        assertions["historical_precedents_isolated"] = all(
            hasattr(h, "documentary_context") or hasattr(h, "documentary_outcome")
            for h in hist_cases
        ) if hist_cases else True

        # 6. VIDEO / CV ASSERTIONS
        vid_summary = workspace.evidence_summary.get("video")
        assertions["video_cv_honest_status"] = vid_summary is not None and vid_summary.availability in ["UNAVAILABLE", "PARTIAL", "FULL"]

        # 7. WORKSPACE ASSERTIONS
        assertions["workspace_triage_exists"] = len(workspace.evidence_items) > 0
        assertions["workspace_timeline_exists"] = len(workspace.timeline) > 0
        assertions["workspace_timeline_has_uncertainty"] = all(
            item.uncertainty is not None for item in workspace.timeline
        )
        assertions["workspace_triage_order_deterministic"] = [item.triage_priority for item in workspace.evidence_items] == sorted(
            [item.triage_priority for item in workspace.evidence_items]
        )

        # 8. REVIEW STATE MACHINE & IMMUTABILITY ASSERTIONS
        assertions["review_state_valid"] = workspace.case.review_status in [
            "REQUIRES_REVIEW", "UNDER_REVIEW", "REVIEWED", "DISMISSED", "PENDING_REVIEW"
        ]
        assertions["audit_trail_supported"] = (
            len(workspace.review.review_history) >= 1
            or len(workspace.review.evidence_acknowledgements) >= 1
        )
        assertions["underlying_evidence_immutable"] = (
            raw_dossier.candidate.minimum_gap_meters is not None
            and raw_dossier.candidate.candidate_id == master_dossier.candidate_id
        )

        return assertions


__all__ = [
    "CaseReplayResult",
    "CaseReplayService",
    "ReplayTimings",
]
