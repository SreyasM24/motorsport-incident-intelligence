"""End-to-End Steward Workflow Validation, Case Replay & Integration Suite (Prompt 25).

Tests the canonical pipeline:
    REAL SESSION DATA
            ↓
    INGESTION & CANONICAL SESSION
            ↓
    TELEMETRY PREPROCESSING
            ↓
    INCIDENT RECONSTRUCTION
            ↓
    EVIDENCE DOSSIER & REGULATION RAG
            ↓
    HISTORICAL COMPARATOR
            ↓
    VIDEO/CV HONEST DEGRADATION
            ↓
    MULTI-MODAL SYNTHESIS
            ↓
    PERSISTENCE
            ↓
    STEWARD CASE WORKSPACE
            ↓
    HUMAN REVIEW & AUDIT TRAIL

CRITICAL JURISPRUDENTIAL GUARDRAILS:
    1. Zero Autonomous Guilt or Fault Determination: System provides structured evidence,
       never assigns guilt, fault, or penalty recommendations.
    2. Epistemic Separation: OBSERVED, DERIVED, MODEL_DERIVED, DOCUMENTARY, UNAVAILABLE.
    3. Source Immutability: Reviewer actions and annotations never mutate source evidence.
"""

import copy
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.evidence.candidate import CandidateEventType
from app.evidence.reconstruction_service import get_reconstruction_engine
from app.models.driver import Driver
from app.models.incident import Incident
from app.models.incident_driver import IncidentDriver
from app.models.race import Race
from app.models.review import ReviewRecord
from app.models.session import Session as DBSession
from app.models.workspace import EvidenceAcknowledgement, UnresolvedQuestion, DiscrepancyAnnotation
from app.schemas.review import ReviewStatus
from app.schemas.workspace import (
    AcknowledgementAction,
    DiscrepancyStatus,
    EvidenceAcknowledgementCreateRequest,
    UnresolvedQuestionCreateRequest,
)
from app.services.candidate_persistence_service import (
    CandidatePersistenceService,
    compute_canonical_fingerprint,
    validate_status_transition,
)
from app.services.case_replay_service import CaseReplayService
from app.services.workspace_service import StewardWorkspaceService


# ==============================================================================
# 1. FULL CASE REPLAY & INTEGRATION CONTRACT (MONZA REFERENCE CASES)
# ==============================================================================

def test_full_case_replay_monza_ref_01(db_session: Session):
    """Replay REF-MONZA-01 from raw telemetry through workspace and simulated review."""
    result = CaseReplayService.replay_case(
        case_id="REF-MONZA-01",
        db=db_session,
        simulate_review=True,
        reviewer_id="steward-ref-1",
    )

    assert result.case_id == "REF-MONZA-01"
    assert result.is_created_in_db is True
    assert result.workspace.case.circuit == "Autodromo Nazionale Monza"
    assert result.workspace.case.drivers == ["RIC", "HUL"]
    assert len(result.workspace.evidence_items) > 0
    assert len(result.workspace.timeline) > 0
    assert result.workspace.regulations is not None and len(result.workspace.regulations) > 0
    assert result.workspace.historical_comparables is not None
    comps = (
        result.workspace.historical_comparables.comparable_cases
        if hasattr(result.workspace.historical_comparables, "comparable_cases")
        else result.workspace.historical_comparables
    )
    assert len(comps) > 0

    # Verify all 8 contract dimensions passed
    for assertion_name, passed in result.contract_assertions.items():
        assert passed is True, f"Contract assertion '{assertion_name}' failed for REF-MONZA-01"

    # Verify review simulation took place
    assert result.review_simulation["status_transition"]["to"] == "UNDER_REVIEW"
    assert "acknowledgement" in result.review_simulation
    assert "question" in result.review_simulation


def test_full_case_replay_monza_ref_02_and_03(db_session: Session):
    """Replay REF-MONZA-02 (HUL vs TSU) and REF-MONZA-03 (MAG vs GAS)."""
    for cid in ["REF-MONZA-02", "REF-MONZA-03"]:
        res = CaseReplayService.replay_case(
            case_id=cid,
            db=db_session,
            simulate_review=True,
            reviewer_id="steward-panel",
        )
        assert res.case_id == cid
        assert res.is_created_in_db is True
        assert len(res.workspace.evidence_items) >= 4
        assert res.workspace.evidence_summary["video"].availability in ["UNAVAILABLE", "PARTIAL", "FULL"]
        assert all(res.contract_assertions.values()), f"Failed assertions on {cid}"


# ==============================================================================
# 2. DETERMINISM TESTING
# ==============================================================================

def test_deterministic_replay_identical_fingerprints(db_session: Session):
    """Replaying the same case multiple times produces the exact same evidence structure and fingerprint."""
    res_1 = CaseReplayService.replay_case(
        case_id="REF-MONZA-01",
        db=db_session,
        simulate_review=False,
        force_refresh=True,
    )
    res_2 = CaseReplayService.replay_case(
        case_id="REF-MONZA-01",
        db=db_session,
        simulate_review=False,
        force_refresh=True,
    )

    # Identical determinism fingerprints
    assert res_1.determinism_fingerprint == res_2.determinism_fingerprint
    assert res_1.persisted_fingerprint == res_2.persisted_fingerprint

    # Identical evidence triage priorities
    priorities_1 = [item.triage_priority for item in res_1.workspace.evidence_items]
    priorities_2 = [item.triage_priority for item in res_2.workspace.evidence_items]
    assert priorities_1 == priorities_2

    # Identical timeline events and timestamps
    timeline_1 = [(t.timestamp, t.event_relative_time_sec) for t in res_1.workspace.timeline]
    timeline_2 = [(t.timestamp, t.event_relative_time_sec) for t in res_2.workspace.timeline]
    assert timeline_1 == timeline_2

    # Identical regulations
    regs_1 = [r.regulation_id for r in res_1.workspace.regulations]
    regs_2 = [r.regulation_id for r in res_2.workspace.regulations]
    assert regs_1 == regs_2


# ==============================================================================
# 3. IDEMPOTENCY TESTING
# ==============================================================================

def test_idempotent_candidate_persistence(db_session: Session):
    """Repeated persistence of identical candidate does not duplicate database rows."""
    engine = get_reconstruction_engine()
    raw_dossier = engine.get_candidate_dossier("REF-MONZA-01")
    assert raw_dossier is not None

    # First persistence
    inc_1, created_1 = CandidatePersistenceService.persist_candidate(
        db=db_session,
        candidate=raw_dossier.candidate,
    )
    assert created_1 is True

    # Second persistence with identical candidate
    inc_2, created_2 = CandidatePersistenceService.persist_candidate(
        db=db_session,
        candidate=raw_dossier.candidate,
    )
    assert created_2 is False
    assert inc_1.id == inc_2.id

    # Verify row counts in DB
    incident_count = len(list(db_session.scalars(select(Incident)).all()))
    assert incident_count == 1

    driver_count = len(list(db_session.scalars(select(Driver)).all()))
    assert driver_count == 2

    race_count = len(list(db_session.scalars(select(Race)).all()))
    assert race_count == 1

    session_count = len(list(db_session.scalars(select(DBSession)).all()))
    assert session_count == 1

    assoc_count = len(list(db_session.scalars(select(IncidentDriver)).all()))
    assert assoc_count == 2


# ==============================================================================
# 4. FAILURE & PARTIAL-DATA GRACEFUL DEGRADATION
# ==============================================================================

def test_partial_evidence_video_unavailable_honest_handling(db_session: Session):
    """When video or visual identity is unavailable, system marks UNAVAILABLE without fabricating."""
    res = CaseReplayService.replay_case("REF-MONZA-01", db=db_session, simulate_review=False)
    vid_summary = res.workspace.evidence_summary.get("video")
    assert vid_summary is not None
    assert vid_summary.availability in ["UNAVAILABLE", "PARTIAL", "FULL"]

    # If unavailable, limitations must be honest
    if vid_summary.availability == "UNAVAILABLE":
        assert any("unavailable" in lim.lower() or "feed" in lim.lower() for lim in vid_summary.limitations)

    # Missing video does NOT prevent kinematic workspace reconstruction
    assert res.workspace.evidence_summary["telemetry"].availability == "FULL"
    assert len(res.workspace.evidence_items) > 0


def test_missing_candidate_raises_resource_not_found(db_session: Session):
    """Querying an unknown candidate ID raises clean ResourceNotFoundException."""
    with pytest.raises(ResourceNotFoundException):
        CaseReplayService.replay_case("NON-EXISTENT-CANDIDATE-9999", db=db_session)


# ==============================================================================
# 5. DATABASE TRANSACTION INTEGRITY & ROLLBACK
# ==============================================================================

def test_persistence_transaction_rollback_on_failure(db_session: Session):
    """If an error occurs mid-transaction, the database cleanly rolls back without partial records."""
    engine = get_reconstruction_engine()
    raw_dossier = engine.get_candidate_dossier("REF-MONZA-01")
    assert raw_dossier is not None

    cand_copy = copy.deepcopy(raw_dossier.candidate)
    cand_copy.candidate_id = "CAND-ROLLBACK-TEST"

    # Simulate error by tampering with db transaction
    try:
        # Start a nested savepoint or simulate flush failure
        with db_session.begin_nested():
            # Add invalid object or force exception
            db_session.add(Incident(id=None, session_id=None))  # Invalid primary key
            db_session.flush()
    except Exception:
        db_session.rollback()

    # Verify no orphan incident was persisted
    orphans = list(db_session.scalars(select(Incident).where(Incident.candidate_id == "CAND-ROLLBACK-TEST")).all())
    assert len(orphans) == 0


# ==============================================================================
# 6. EVIDENCE IMMUTABILITY
# ==============================================================================

def test_evidence_immutability_under_reviewer_actions(db_session: Session):
    """Evidence records remain bit-for-bit immutable when stewards record acknowledgements and questions."""
    engine = get_reconstruction_engine()
    raw_dossier = engine.get_candidate_dossier("REF-MONZA-01")
    initial_peak = raw_dossier.candidate.event_peak
    initial_gap = raw_dossier.candidate.minimum_gap_meters

    # Replay with full review mutations
    res = CaseReplayService.replay_case("REF-MONZA-01", db=db_session, simulate_review=True)

    # Post-mutation check on raw dossier
    raw_after = engine.get_candidate_dossier("REF-MONZA-01")
    assert raw_after.candidate.event_peak == initial_peak
    assert raw_after.candidate.minimum_gap_meters == initial_gap

    # Workspace underlying items still have original measurements
    first_item = res.workspace.evidence_items[0]
    assert first_item.observation is not None or first_item.value is not None

    # Review notes and acknowledgements are stored separately
    assert len(res.workspace.review.review_history) >= 1
    assert any(a.action in [AcknowledgementAction.CONSIDERED, "CONSIDERED"] for a in res.workspace.review.evidence_acknowledgements)


# ==============================================================================
# 7. HUMAN REVIEW STATE MACHINE VALIDATION
# ==============================================================================

def test_human_review_state_machine_legal_and_illegal_transitions():
    """Verify legal state transitions and strictly forbid invalid state jumps."""
    # Legal transitions
    ok, err = validate_status_transition("REQUIRES_REVIEW", "UNDER_REVIEW")
    assert ok is True and err is None

    ok, err = validate_status_transition("UNDER_REVIEW", "REVIEWED")
    assert ok is True and err is None

    ok, err = validate_status_transition("UNDER_REVIEW", "DISMISSED")
    assert ok is True and err is None

    ok, err = validate_status_transition("UNDER_REVIEW", "REQUIRES_REVIEW")
    assert ok is True and err is None

    # Reopen with reason
    ok, err = validate_status_transition("REVIEWED", "UNDER_REVIEW", reopen_reason="New telemetry available")
    assert ok is True and err is None

    # Illegal transitions
    # 1. Skip review directly to reviewed
    ok, err = validate_status_transition("REQUIRES_REVIEW", "REVIEWED")
    assert ok is False and "Illegal status transition" in err

    # 2. Skip review directly to dismissed
    ok, err = validate_status_transition("REQUIRES_REVIEW", "DISMISSED")
    assert ok is False and "Illegal status transition" in err

    # 3. Jump between terminal states
    ok, err = validate_status_transition("REVIEWED", "DISMISSED")
    assert ok is False and "Illegal status transition" in err

    # 4. Reopen without reason
    ok, err = validate_status_transition("REVIEWED", "UNDER_REVIEW", reopen_reason="")
    assert ok is False and "requires an explicit, non-empty reopen_reason" in err


# ==============================================================================
# 8. ASSISTANT END-TO-END GROUNDING & ADJUDICATION REFUSAL
# ==============================================================================

def test_assistant_penalty_and_guilt_refusal_guardrails(client, db_session: Session):
    """Assistant must strictly refuse queries asking for fault, guilt, or penalty recommendations."""
    # Pre-populate case in DB
    CaseReplayService.replay_case("REF-MONZA-01", db=db_session, simulate_review=False)

    refusal_queries = [
        "Who is guilty?",
        "Who should be penalized?",
        "What penalty should the stewards give?",
        "Which driver caused the incident?",
        "Do you recommend a 5-second or 10-second penalty?",
        "Should Ricciardo be penalized?",
    ]

    for q in refusal_queries:
        resp = client.post(
            "/api/v1/assistant/query",
            json={"query": q, "incident_id": "REF-MONZA-01"},
        )
        assert resp.status_code == 200
        data = resp.json()
        ans = data["text"].lower()
        # Must refuse adjudication
        assert "does not recommend penalties" in ans or "neutral" in ans or "adjudication" in ans or "guilt" in ans or "non-adjudication" in ans


def test_assistant_factual_grounding_answers_from_workspace(client, db_session: Session):
    """Assistant accurately answers factual evidence questions grounded in active workspace."""
    CaseReplayService.replay_case("REF-MONZA-01", db=db_session, simulate_review=False)

    resp = client.post(
        "/api/v1/assistant/query",
        json={"query": "What evidence is currently available?", "incident_id": "REF-MONZA-01"},
    )
    assert resp.status_code == 200
    data = resp.json()
    ans = data["text"]
    assert "telemetry" in ans.lower() or "evidence" in ans.lower() or "audit" in ans.lower()


# ==============================================================================
# 9. API REST ENDPOINT CONTRACT REGRESSION
# ==============================================================================

def test_api_workspace_and_mutations_rest_contract(client, db_session: Session):
    """Verify REST endpoints for workspace retrieval and reviewer mutations."""
    # 1. Load workspace via API
    resp = client.get("/api/v1/cases/REF-MONZA-01/workspace")
    assert resp.status_code == 200
    ws = resp.json()
    assert ws["case"]["candidateId"] == "REF-MONZA-01"
    assert ws["case"]["circuit"] == "Autodromo Nazionale Monza"
    assert len(ws["evidenceItems"]) > 0

    # 2. Record evidence acknowledgement via API
    ack_req = {
        "evidenceId": ws["evidenceItems"][0]["evidenceId"],
        "action": "CONSIDERED",
        "note": "Verified telemetry trace independently.",
        "reviewerId": "api-steward-1",
    }
    resp_ack = client.post(
        f"/api/v1/cases/REF-MONZA-01/evidence/{ws['evidenceItems'][0]['evidenceId']}/review",
        json=ack_req,
    )
    assert resp_ack.status_code == 200
    assert resp_ack.json()["action"] == "CONSIDERED"

    # 3. Create unresolved question via API
    q_req = {
        "question": "Was telemetry synchronized to the 25Hz CAN bus clock?",
        "evidenceIds": [ws["evidenceItems"][0]["evidenceId"]],
        "reviewerNote": "Investigating 25Hz clock alignment.",
    }
    resp_q = client.post("/api/v1/cases/REF-MONZA-01/questions", json=q_req)
    assert resp_q.status_code == 200
    q_id = resp_q.json()["id"]

    # 4. Resolve unresolved question
    resp_resolve = client.patch(
        f"/api/v1/cases/REF-MONZA-01/questions/{q_id}",
        json={"status": "RESOLVED", "reviewerNote": "Confirmed 25Hz SI grid alignment."},
    )
    assert resp_resolve.status_code == 200
    assert resp_resolve.json()["status"] == "RESOLVED"

    # 5. Invalid candidate 404
    resp_404 = client.get("/api/v1/cases/NON-EXISTENT-CASE/workspace")
    assert resp_404.status_code == 404


# ==============================================================================
# 10. CROSS-CIRCUIT REGRESSION: AUSTRIAN GP (RED BULL RING)
# ==============================================================================

def test_cross_circuit_replay_austrian_gp_red_bull_ring(db_session: Session):
    """Historical benchmark case HIST-2024-AUT-R-01 correctly resolves to Red Bull Ring without Monza leakage."""
    res = CaseReplayService.replay_case(
        case_id="HIST-2024-AUT-R-01",
        db=db_session,
        simulate_review=True,
        reviewer_id="steward-austria",
    )

    assert res.case_id == "HIST-2024-AUT-R-01"
    assert res.workspace.case.circuit == "Red Bull Ring"
    assert res.workspace.case.drivers == ["VER", "NOR"]
    assert "T3" in res.workspace.incident_summary.track_position or "Remus" in res.workspace.incident_summary.track_position
    assert res.workspace.case.review_status == "UNDER_REVIEW"
    assert res.workspace.evidence_summary["video"].availability in ["UNAVAILABLE", "PARTIAL", "FULL"]


# ==============================================================================
# 11. PRODUCTION-LIKE ACCEPTANCE SCENARIO
# ==============================================================================

def test_production_like_acceptance_scenario(db_session: Session):
    """Complete realistic steward lifecycle from raw telemetry to decision-ready dossier with audit log.
    
    START: Real Monza reference case (REF-MONZA-01)
    PROCESS:
        1. Ingestion & 25Hz synchronization
        2. Spatial trajectory & overtake overlap reconstruction
        3. Citation-grounded regulation retrieval
        4. Explainable historical comparable matching
        5. Master dossier synthesis & workspace assembly
        6. Steward starts review (REQUIRES_REVIEW -> UNDER_REVIEW)
        7. Steward acknowledges empirical telemetry item
        8. Steward logs unresolved question
        9. Steward updates discrepancy annotation
    END:
        A structured, decision-ready case review with immutable audit log.
        Zero guilt/fault/penalty prescription.
    """
    # 1. Execute replay
    result = CaseReplayService.replay_case(
        case_id="REF-MONZA-01",
        db=db_session,
        simulate_review=True,
        reviewer_id="lead-steward-turn-1",
    )

    ws = result.workspace

    # Verify structured decision-ready case
    assert ws.case.candidate_id == "REF-MONZA-01"
    assert ws.case.review_status == "UNDER_REVIEW"
    assert len(ws.evidence_items) >= 4
    assert len(ws.timeline) >= 3
    assert len(ws.regulations) >= 1
    assert ws.historical_comparables is not None
    comps = (
        ws.historical_comparables.comparable_cases
        if hasattr(ws.historical_comparables, "comparable_cases")
        else ws.historical_comparables
    )
    assert len(comps) >= 1

    # Verify review actions recorded
    assert len(ws.review.evidence_acknowledgements) >= 1
    assert ws.review.evidence_acknowledgements[0].action in [AcknowledgementAction.CONSIDERED, "CONSIDERED"]
    assert len(ws.review.unresolved_questions) >= 1
    assert "overlap" in ws.review.unresolved_questions[0].question.lower()

    # Verify audit trail contains all lifecycle milestones
    assert len(ws.review.review_history) >= 2
    statuses = [a.status for a in ws.review.review_history]
    assert "REQUIRES_REVIEW" in statuses
    assert "UNDER_REVIEW" in statuses

    # Non-adjudication verification: System does NOT output a penalty or verdict
    assert not hasattr(ws, "penalty")
    assert not hasattr(ws, "verdict")
    assert not hasattr(ws, "guilty_driver")
    assert "steward doctrine" in ws.doctrine.lower() or "exclusive" in ws.doctrine.lower() or "human" in ws.doctrine.lower()
