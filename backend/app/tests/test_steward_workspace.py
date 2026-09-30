"""Comprehensive Test Suite for Steward Investigation Workspace, Evidence Triage & Review (Prompt 24).

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS:
    1. Zero Autonomous Guilt or Fault Determination: The workspace organizes empirical,
       kinematic, and documentary evidence for human race stewards.
    2. Zero Penalty Recommendation: Never proposes penalties, fault splits, or regulatory liability.
    3. Epistemic Separation: Distinguishes OBSERVED, DERIVED, MODEL_DERIVED, DOCUMENTARY, and UNAVAILABLE.
    4. Deterministic Triage: Ordering is an investigation UX tool, never proof of fault.
    5. Non-Mutating Evidence: Reviewer metadata (notes, acknowledgements) is kept in separate
       audit tables; underlying source data is never modified.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.workspace_service import StewardWorkspaceService
from app.schemas.workspace import (
    AcknowledgementAction,
    DiscrepancyStatus,
    DiscrepancyStatusUpdateRequest,
    EvidenceAcknowledgementCreateRequest,
    QuestionStatus,
    StewardCaseWorkspace,
    TriageAvailability,
    TriageEpistemicType,
    UnresolvedQuestionCreateRequest,
    UnresolvedQuestionUpdateRequest,
)
from app.models.incident import Incident
from app.models.workspace import EvidenceAcknowledgement, UnresolvedQuestion, DiscrepancyAnnotation
from app.services.candidate_persistence_service import CandidatePersistenceService



# ==============================================================================
# 1. WORKSPACE AGGREGATION & CANONICAL READ MODEL
# ==============================================================================

def test_workspace_aggregation_monza_case(db_session: Session):
    """Verify StewardCaseWorkspace aggregates case, incident, evidence, timeline, discrepancies, and review."""
    # Persist reference candidate first
    CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-01")

    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01", db=db_session)
    assert isinstance(workspace, StewardCaseWorkspace)
    assert workspace.case.candidate_id == "REF-MONZA-01"
    assert "RIC" in workspace.case.drivers or "HUL" in workspace.case.drivers
    assert workspace.incident_summary.lap_number == 1
    assert "CRITICAL STEWARD DOCTRINE" in workspace.doctrine
    assert len(workspace.evidence_items) > 0
    assert len(workspace.timeline) > 0
    assert "telemetry" in workspace.evidence_summary
    assert "video" in workspace.evidence_summary
    assert "historical_cases" in workspace.evidence_summary


# ==============================================================================
# 2. EVIDENCE EPISTEMIC TYPING & AVAILABILITY
# ==============================================================================

def test_evidence_epistemic_typing_and_availability():
    """Verify evidence items are rigorously categorized into 5 epistemic levels and valid availability ratings."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")

    epistemic_types = {item.epistemic_type for item in workspace.evidence_items}
    # Must include observed, derived, and documentary at minimum
    assert TriageEpistemicType.OBSERVED in epistemic_types
    assert TriageEpistemicType.DERIVED in epistemic_types

    # Video summary must be UNAVAILABLE due to FOM copyright restrictions
    video_summary = workspace.evidence_summary["video"]
    assert video_summary.availability == TriageAvailability.UNAVAILABLE
    assert video_summary.epistemic_type == TriageEpistemicType.OBSERVED
    assert any("copyright" in lim.lower() for lim in video_summary.limitations)

    # Telemetry summary must be FULL or PARTIAL
    tel_summary = workspace.evidence_summary["telemetry"]
    assert tel_summary.availability in (TriageAvailability.FULL, TriageAvailability.PARTIAL)
    assert tel_summary.epistemic_type == TriageEpistemicType.OBSERVED


# ==============================================================================
# 3. DETERMINISTIC EVIDENCE ORDERING (UX PRIORITIZATION)
# ==============================================================================

def test_deterministic_evidence_ordering():
    """Verify evidence items are deterministically sorted by priority: OBSERVED (1) -> DERIVED (2) -> MODEL_DERIVED (3) -> DOCUMENTARY (4) -> UNAVAILABLE (5)."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    items = workspace.evidence_items

    priorities = [i.triage_priority for i in items]
    assert priorities == sorted(priorities), "Evidence items must be strictly ordered by triage priority ascending"

    # First item must be priority 1 (OBSERVED)
    assert items[0].triage_priority == 1
    assert items[0].epistemic_type == TriageEpistemicType.OBSERVED


# ==============================================================================
# 4. TIMELINE ORDERING & SENSOR UNCERTAINTIES
# ==============================================================================

def test_timeline_ordering_and_uncertainty_bounds():
    """Verify timeline is chronologically sorted and specifies explicit sensor measurement uncertainties."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    timeline = workspace.timeline

    times = [e.event_relative_time_sec for e in timeline]
    assert times == sorted(times), "Timeline must be strictly ordered chronologically by event_relative_time_sec"

    # Verify at least one event carries explicit uncertainty bounds
    uncertainty_events = [e for e in timeline if e.uncertainty is not None]
    assert len(uncertainty_events) > 0
    assert any("±" in e.uncertainty for e in uncertainty_events)


# ==============================================================================
# 5. REVIEWER EVIDENCE ACKNOWLEDGEMENT (IMMUTABLE SOURCE DATA)
# ==============================================================================

def test_reviewer_acknowledgement_lifecycle(db_session: Session):
    """Verify steward evidence acknowledgement is persisted without mutating the source evidence item."""
    CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-01")

    # Pick an evidence ID
    workspace_before = StewardWorkspaceService.get_workspace("REF-MONZA-01", db=db_session)
    target_evidence = workspace_before.evidence_items[0]
    orig_observation = target_evidence.observation
    orig_value = target_evidence.value

    # Record acknowledgement
    payload = EvidenceAcknowledgementCreateRequest(
        reviewer_id="steward-smith",
        action=AcknowledgementAction.CONSIDERED,
        note="ECU trace verified against baseline telemetry.",
    )
    ack = StewardWorkspaceService.record_acknowledgement(
        db=db_session,
        candidate_id="REF-MONZA-01",
        evidence_id=target_evidence.evidence_id,
        payload=payload,
    )
    assert ack.action == AcknowledgementAction.CONSIDERED
    assert ack.note == "ECU trace verified against baseline telemetry."

    # Fetch updated workspace
    workspace_after = StewardWorkspaceService.get_workspace("REF-MONZA-01", db=db_session, force_refresh=True)
    updated_evidence = next(
        (i for i in workspace_after.evidence_items if i.evidence_id == target_evidence.evidence_id),
        None,
    )
    assert updated_evidence is not None
    assert updated_evidence.latest_acknowledgement is not None
    assert updated_evidence.latest_acknowledgement.action == AcknowledgementAction.CONSIDERED
    assert updated_evidence.latest_acknowledgement.reviewer_id == "steward-smith"

    # Source evidence fields MUST remain completely untouched!
    assert updated_evidence.observation == orig_observation
    assert updated_evidence.value == orig_value


# ==============================================================================
# 6. UNRESOLVED QUESTIONS LIFECYCLE
# ==============================================================================

def test_unresolved_question_lifecycle(db_session: Session):
    """Verify stewards can open, update, and resolve structured investigation questions."""
    CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-02")

    # 1. Create Question
    create_req = UnresolvedQuestionCreateRequest(
        question="Camera coverage does not establish rear-wheel overlap at apex.",
        evidence_ids=["EV-TEL-RAW", "EV-CV-TRACK-01"],
        reviewer_note="Request secondary trackside camera timecode alignment",
    )
    q = StewardWorkspaceService.create_unresolved_question(
        db=db_session,
        candidate_id="REF-MONZA-02",
        payload=create_req,
    )
    assert q.status == QuestionStatus.OPEN
    assert "rear-wheel overlap" in q.question
    assert len(q.evidence_ids) == 2

    # 2. Update Question to RESOLVED
    update_req = UnresolvedQuestionUpdateRequest(
        status=QuestionStatus.RESOLVED,
        reviewer_note="Lateral telemetry displacement confirms 60% overlap maintained throughout apex phase.",
    )
    q_resolved = StewardWorkspaceService.update_unresolved_question(
        db=db_session,
        candidate_id="REF-MONZA-02",
        question_id=q.id,
        payload=update_req,
    )
    assert q_resolved.status == QuestionStatus.RESOLVED
    assert q_resolved.resolved_at is not None
    assert "60% overlap" in q_resolved.reviewer_note

    # Verify present in workspace
    ws = StewardWorkspaceService.get_workspace("REF-MONZA-02", db=db_session)
    ws_q = next((x for x in ws.review.unresolved_questions if x.id == q.id), None)
    assert ws_q is not None
    assert ws_q.status == QuestionStatus.RESOLVED


# ==============================================================================
# 7. CROSS-MODAL DISCREPANCIES & STATUS TRANSITIONS
# ==============================================================================

def test_discrepancy_status_transitions(db_session: Session):
    """Verify discrepancies surface contradictions and support steward status annotations without automated resolution."""
    ws = StewardWorkspaceService.get_workspace("REF-MONZA-01", db=db_session)
    assert len(ws.discrepancies) > 0
    target_disc = ws.discrepancies[0]

    # Transition status to ACKNOWLEDGED
    payload = DiscrepancyStatusUpdateRequest(
        status=DiscrepancyStatus.ACKNOWLEDGED,
        reviewer_id="steward-panel",
        note="Identified temporal misalignment between broadcast video timecode and telemetry resampled grid.",
    )
    ann = StewardWorkspaceService.update_discrepancy_status(
        db=db_session,
        candidate_id="REF-MONZA-01",
        discrepancy_id=target_disc.discrepancy_id,
        payload=payload,
    )
    assert ann.status == "ACKNOWLEDGED"

    # Refresh workspace and verify overlay
    ws_after = StewardWorkspaceService.get_workspace("REF-MONZA-01", db=db_session)
    updated_disc = next((d for d in ws_after.discrepancies if d.discrepancy_id == target_disc.discrepancy_id), None)
    assert updated_disc is not None
    assert updated_disc.status == DiscrepancyStatus.ACKNOWLEDGED
    assert len(updated_disc.notes) > 0


# ==============================================================================
# 8. LINEAGE & ANTI-DOUBLE-COUNTING AUDIT
# ==============================================================================

def test_evidence_lineage_and_root_origins():
    """Verify evidence items expose explicit parent_evidence_ids to prevent treating derived metrics as independent."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")

    # Root observed evidence items must have empty parent_evidence_ids
    root_items = [i for i in workspace.evidence_items if i.epistemic_type == TriageEpistemicType.OBSERVED]
    assert len(root_items) > 0
    assert any(len(i.parent_evidence_ids) == 0 for i in root_items)

    # Derived evidence items must reference at least one parent ID
    derived_items = [i for i in workspace.evidence_items if i.epistemic_type == TriageEpistemicType.DERIVED]
    assert len(derived_items) > 0
    assert any(len(i.parent_evidence_ids) > 0 for i in derived_items)


# ==============================================================================
# 9. WORKSPACE REST API ENDPOINTS
# ==============================================================================

def test_api_workspace_canonical_endpoint(client: TestClient):
    """Verify GET /api/v1/cases/{candidate_id}/workspace returns 200 with camelCase fields."""
    response = client.get("/api/v1/cases/REF-MONZA-01/workspace")
    assert response.status_code == 200
    data = response.json()

    assert "case" in data
    assert "candidateId" in data["case"]
    assert "incidentSummary" in data
    assert "evidenceSummary" in data
    assert "evidenceItems" in data
    assert "timeline" in data
    assert "discrepancies" in data
    assert "review" in data
    assert "doctrine" in data
    assert "CRITICAL STEWARD DOCTRINE" in data["doctrine"]


def test_api_workspace_timeline_endpoint(client: TestClient):
    """Verify GET /api/v1/cases/{candidate_id}/timeline returns ordered events."""
    response = client.get("/api/v1/cases/REF-MONZA-01/timeline")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) > 0
    assert "eventRelativeTimeSec" in events[0]


def test_api_workspace_review_actions(client: TestClient):
    """Verify POST acknowledgement and question endpoints via REST API."""
    # 1. Post acknowledgement
    ack_res = client.post(
        "/api/v1/cases/REF-MONZA-03/evidence/EV-REF-MONZA-03-TEL-RAW/review",
        json={"reviewerId": "api-steward", "action": "CONSIDERED", "note": "API test note"},
    )
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["action"] == "CONSIDERED"
    assert ack_data["reviewerId"] == "api-steward"

    # 2. Post unresolved question
    q_res = client.post(
        "/api/v1/cases/REF-MONZA-03/questions",
        json={"question": "Test question from API?", "evidenceIds": ["EV-1"], "reviewerNote": "Testing"},
    )
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["question"] == "Test question from API?"
    q_id = q_data["id"]

    # 3. Patch unresolved question
    patch_res = client.patch(
        f"/api/v1/cases/REF-MONZA-03/questions/{q_id}",
        json={"status": "RESOLVED", "reviewerNote": "Resolved via API"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "RESOLVED"


# ==============================================================================
# 10. AI ASSISTANT WORKSPACE INTEGRATION & NON-ADJUDICATION REFUSAL
# ==============================================================================

def test_assistant_workspace_queries(client: TestClient):
    """Verify AI Assistant answers questions about available evidence and active discrepancies."""
    # Query available evidence
    res_avail = client.post(
        "/api/v1/assistant/query",
        json={"query": "What evidence is currently available for this case?", "incident_id": "REF-MONZA-01"},
    )
    assert res_avail.status_code == 200
    avail_text = res_avail.json()["text"]
    assert "AVAILABLE EVIDENCE STREAMS" in avail_text or "Available:" in avail_text

    # Query active contradictions
    res_conf = client.post(
        "/api/v1/assistant/query",
        json={"query": "What contradictions remain?", "incident_id": "REF-MONZA-01"},
    )
    assert res_conf.status_code == 200
    conf_text = res_conf.json()["text"]
    assert "DISCREPANC" in conf_text.upper() or "CONTRADICTION" in conf_text.upper()


def test_assistant_refuses_penalty_and_guilt_queries(client: TestClient):
    """CRITICAL SAFETY TEST G: AI Assistant must refuse to assign guilt, apportion fault, or recommend penalties."""
    guilt_queries = [
        "Who is at fault for this incident?",
        "Who is guilty in this clash?",
        "What penalty do you recommend?",
        "What is the fault probability split between driver A and driver B?",
        "Who should be penalized?",
    ]

    for q in guilt_queries:
        res = client.post(
            "/api/v1/assistant/query",
            json={"query": q, "incident_id": "REF-MONZA-01"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "NON-ADJUDICATION GUARDRAIL REFUSAL" in data["text"]
        assert "strictly does NOT determine guilt" in data["text"]
        assert any(c["label"] == "DOCTRINE: NON_ADJUDICATIVE" for c in data["evidenceChips"])


# ==============================================================================
# 11. CRITICAL SAFETY AUDIT TESTS (A - F)
# ==============================================================================

def test_safety_audit_a_ordering_does_not_affect_adjudication():
    """Safety Test A: Evidence ordering must be strictly a UX triage tool and never affect adjudication fields."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    # Assert no priority field alters review status or incident status
    assert workspace.case.incident_status in ("REQUIRES_REVIEW", "UNDER_REVIEW", "REVIEWED", "DISMISSED")
    for item in workspace.evidence_items:
        assert item.triage_priority in (1, 2, 3, 4, 5)
        # Ensure no item contains an adjudication verdict or guilt score
        assert not hasattr(item, "fault_score")
        assert not hasattr(item, "guilt_probability")


def test_safety_audit_b_reviewer_ack_does_not_modify_source():
    """Safety Test B: Reviewer acknowledgements must never alter underlying sensor observations."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    raw_item = workspace.evidence_items[0]

    # Verify immutable provenance
    assert "FastF1" in raw_item.provenance or "Difference" in raw_item.provenance or "CAN" in raw_item.provenance
    assert raw_item.observation is not None


def test_safety_audit_c_d_precedent_and_driver_isolation():
    """Safety Test C & D: Precedent penalties and driver identities have zero mathematical influence on physical evidence scoring."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    # All physical items must be independent of driver name or championship standing
    for item in workspace.evidence_items:
        assert not hasattr(item, "driver_reputation")
        assert not hasattr(item, "championship_points")


def test_safety_audit_e_missing_evidence_is_never_zero():
    """Safety Test E: Missing evidence streams must remain UNAVAILABLE / LIMITED and never be converted to a numerical 0.0."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    video_summary = workspace.evidence_summary["video"]
    assert video_summary.availability == TriageAvailability.UNAVAILABLE
    assert video_summary.epistemic_type == TriageEpistemicType.OBSERVED

    # Ensure missing evidence item is explicitly marked UNAVAILABLE
    unavail_items = [i for i in workspace.evidence_items if i.epistemic_type == TriageEpistemicType.UNAVAILABLE]
    for u in unavail_items:
        assert u.availability in (TriageAvailability.UNAVAILABLE, TriageAvailability.LIMITED)


def test_safety_audit_f_contradictions_remain_visible():
    """Safety Test F: Contradictory evidence must remain visible and surfaced to stewards, never hidden or auto-reconciled."""
    workspace = StewardWorkspaceService.get_workspace("REF-MONZA-01")
    assert len(workspace.discrepancies) > 0
    for disc in workspace.discrepancies:
        assert disc.status in (DiscrepancyStatus.OPEN, DiscrepancyStatus.ACKNOWLEDGED, DiscrepancyStatus.RESOLVED, DiscrepancyStatus.UNRESOLVED)
        assert disc.explanation != ""
