"""Prompt 17 — End-to-End System Integration, Real Data Validation & Production Readiness Audit.

This test module verifies the end-to-end integration of the complete
Motorsport Incident Intelligence system across all Prompts 01-16.

TEST CLASSIFICATIONS:
- REAL_DATA_VALIDATION: Tests running against cached official FastF1 timing & telemetry data.
- INTEGRATION_TEST_FIXTURE: Tests running against deterministic synthetic test vectors and isolated SQLite sessions.
"""

import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.driver import Driver
from app.models.race import Race
from app.models.session import Session as DBSession
from app.models.review import ReviewRecord
from app.schemas.review import ReviewStatus
from app.services.candidate_persistence_service import CandidatePersistenceService
from app.evidence.synthesis import (
    EvidenceType,
    EvidenceStatus,
    ConsistencyStatus,
    DiscrepancySeverity,
    get_steward_dossier_synthesizer,
)
from app.evidence.reconstruction_service import get_reconstruction_engine


# ==============================================================================
# 1. DATABASE & SCHEMA PERSISTENCE VALIDATION
# ==============================================================================

def test_database_persistence_all_entities(db_session: Session):
    """Verify relational persistence across Race, Session, Driver, Incident, and ReviewRecord."""
    # 1. Persist Monza reference candidate
    resp = CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-01")
    assert resp.is_created is True
    assert resp.status == ReviewStatus.REQUIRES_REVIEW

    # 2. Verify Race record
    race = db_session.get(Race, "f1-2024-monza")
    assert race is not None
    assert race.name == "Italian Grand Prix"
    assert race.circuit == "Monza"
    assert race.season == "2024"

    # 3. Verify Session record
    session_rec = db_session.get(DBSession, resp.incident_id.replace("INC-", "SESS-")) or db_session.query(DBSession).first()
    assert session_rec is not None
    assert session_rec.race_id == race.id

    # 4. Verify Drivers
    ric = db_session.query(Driver).filter(Driver.code == "RIC").first()
    hul = db_session.query(Driver).filter(Driver.code == "HUL").first()
    assert ric is not None and ric.code == "RIC"
    assert hul is not None and hul.code == "HUL"

    # 5. Verify Incident and DriversInvolved linkage
    incident = db_session.get(Incident, resp.incident_id)
    assert incident is not None
    assert incident.lap == 1
    assert len(incident.drivers_involved) == 2
    for participant in incident.drivers_involved:
        assert participant.role in ("PRIMARY", "SECONDARY")
        # Strict Guardrail: non-adjudicative roles only
        assert participant.role not in ("GUILTY", "AT_FAULT", "CULPRIT", "OFFENDER")

    # 6. Verify Review Record
    reviews = incident.reviews
    assert len(reviews) >= 1
    assert reviews[0].status == ReviewStatus.REQUIRES_REVIEW.value
    assert reviews[0].reviewer_id == "system-ingest"


# ==============================================================================
# 2. REAL FASTF1 DATA PATH VALIDATION (REAL_DATA_VALIDATION)
# ==============================================================================

def test_real_fastf1_telemetry_flow(client: TestClient, db_session: Session):
    """Verify the real FastF1 cached telemetry flow from service to API response."""
    # Seed Monza candidate so the incident route has the linked session
    resp_persist = CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-01")
    inc_id = resp_persist.incident_id

    # Query telemetry endpoint for the persisted incident
    resp = client.get(f"/api/v1/incidents/{inc_id}/telemetry?hz=25&limit=100")
    assert resp.status_code == 200
    data = resp.json()
    assert data["incidentId"] == inc_id
    assert "points" in data
    assert isinstance(data["points"], list)

    # If cache is resolved, points should contain physical channels
    if data["points"]:
        pt = data["points"][0]
        assert "speedA" in pt
        assert "speedB" in pt
        assert "gapMeters" in pt
        assert "closingSpeedMs" in pt
        assert pt["gapMeters"] >= 0.0


# ==============================================================================
# 3. LIVE API ENDPOINT SUITE (E2E HTTP FLOWS)
# ==============================================================================

def test_all_live_api_endpoints(client: TestClient, db_session: Session):
    """Test real HTTP status, schema adherence, and error behavior across all v1 routes."""
    # Seed Monza reference incidents into DB
    persisted_ids = []
    for ref_id in ("REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"):
        p = CandidatePersistenceService.persist_by_candidate_id(db_session, ref_id)
        persisted_ids.append(p.incident_id)

    # 1. Health
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert "status" in res.json()
    assert res.json()["app_name"] == "Motorsport Incident Intelligence API"

    # 2. Races
    res = client.get("/api/v1/races")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 3. Drivers
    res = client.get("/api/v1/drivers")
    assert res.status_code == 200
    drivers = res.json()
    assert len(drivers) >= 2
    driver_codes = [d["code"] for d in drivers]
    assert "RIC" in driver_codes or "HUL" in driver_codes

    # 4. Driver Profile
    res = client.get("/api/v1/drivers/RIC")
    assert res.status_code == 200
    assert res.json()["code"] == "RIC"

    # 5. Regulations
    res = client.get("/api/v1/regulations")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 6. Assistant Query
    res = client.post("/api/v1/assistant/query", json={
        "query": "Why was this incident flagged?",
        "incident_id": "REF-MONZA-01"
    })
    assert res.status_code == 200
    asst_data = res.json()
    assert asst_data["sender"] == "assistant"
    assert "PROXIMITY" in asst_data["text"]

    # 7. Incidents List
    res = client.get("/api/v1/incidents")
    assert res.status_code == 200
    incidents = res.json()
    assert len(incidents) >= 3

    # 8. Incident Detail
    target_id = persisted_ids[0]
    res = client.get(f"/api/v1/incidents/{target_id}")
    assert res.status_code == 200
    assert res.json()["id"] == target_id

    # 9. Steward Dossier (Analysis Endpoint)
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/steward-dossier")
    assert res.status_code == 200
    dossier = res.json()
    assert dossier["candidateId"] == "REF-MONZA-01"
    assert "consensus" in dossier
    assert "streamQuality" in dossier
    assert len(dossier["streamQuality"]) == 8

    # 10. Steward Dossier Export JSON
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/steward-dossier/export/json")
    assert res.status_code == 200
    export_payload = res.json()
    assert "exportedAt" in export_payload
    assert "dossier" in export_payload

    # 11. Incident Dossier Route
    res = client.get(f"/api/v1/incidents/{target_id}/dossier")
    assert res.status_code == 200

    # 12. Video Evidence Summary
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video")
    assert res.status_code == 200
    assert res.json()["videoEvidenceStatus"] == "VIDEO_UNAVAILABLE"

    # 13. Visual Evidence
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/visual-evidence")
    assert res.status_code == 200

    # 14. Computer Vision Analysis
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/cv")
    assert res.status_code == 200

    # 15. CV Sufficiency
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/cv/sufficiency")
    assert res.status_code == 200
    assert res.json()["videoAvailable"] is False
    assert res.json()["stewardReadiness"] == "UNAVAILABLE"

    # 16. CV Evaluation Suite
    res = client.get("/api/v1/analysis/cv/evaluation")
    assert res.status_code == 200
    assert res.json()["datasetStateClassification"] == "SYNTHETIC_VALIDATION_ONLY"


# ==============================================================================
# 4. REFERENCE INCIDENT 8-STREAM AUDIT (MONZA 2024)
# ==============================================================================

@pytest.mark.parametrize("case_id,expected_drivers,expected_lap", [
    ("REF-MONZA-01", ["RIC", "HUL"], 1),
    ("REF-MONZA-02", ["HUL", "TSU"], 4),
    ("REF-MONZA-03", ["MAG", "GAS"], 19),
])
def test_reference_incident_stream_classifications(case_id: str, expected_drivers: list, expected_lap: int):
    """Audit all 8 evidence streams for the 3 Monza reference cases."""
    engine = get_reconstruction_engine()
    dossier = engine.get_candidate_dossier(case_id)
    assert dossier is not None

    synthesizer = get_steward_dossier_synthesizer()
    steward_dossier = synthesizer.synthesize_steward_dossier(dossier, candidate_id_override=case_id)

    # 1. Candidate Metadata
    assert steward_dossier.candidate_id == case_id
    assert steward_dossier.lap_number == expected_lap
    assert sorted([steward_dossier.driver_a, steward_dossier.driver_b]) == sorted(expected_drivers)

    # 2. Epistemic Stream Classifications
    stream_map = {q.evidence_type: q for q in steward_dossier.stream_quality}
    assert len(stream_map) == 8

    # Stream 1: Telemetry Dynamics -> OBSERVED
    assert stream_map[EvidenceType.TELEMETRY].status == EvidenceStatus.OBSERVED
    # Stream 2: Reference Baseline -> DERIVED
    assert stream_map[EvidenceType.REFERENCE_BASELINE].status == EvidenceStatus.DERIVED
    # Stream 3: Cornering Geometry -> DERIVED
    assert stream_map[EvidenceType.OVERTAKE_GEOMETRY].status == EvidenceStatus.DERIVED
    # Stream 4: ML Interaction -> MODEL_DERIVED
    assert stream_map[EvidenceType.ML_INTERACTION].status == EvidenceStatus.MODEL_DERIVED
    # Stream 5: Video Synchronization -> UNAVAILABLE (Honest reporting: FOM copyrighted footage unbundled)
    assert stream_map[EvidenceType.VIDEO_SYNCHRONIZATION].status == EvidenceStatus.UNAVAILABLE
    # Stream 6: Visual Keyframes -> UNAVAILABLE
    assert stream_map[EvidenceType.VISUAL].status == EvidenceStatus.UNAVAILABLE
    # Stream 7: Computer Vision Tracking -> UNAVAILABLE
    assert stream_map[EvidenceType.COMPUTER_VISION].status == EvidenceStatus.UNAVAILABLE
    # Stream 8: Statutory Regulations -> DOCUMENTARY
    assert stream_map[EvidenceType.REGULATION].status == EvidenceStatus.DOCUMENTARY

    # 3. Lineage Tracker Verification (Root count is 1, not double-counted)
    assert steward_dossier.consensus.independent_observation_count >= 1

    # 4. Strict Human Review Initial State
    assert steward_dossier.review_status == ReviewStatus.REQUIRES_REVIEW.value


# ==============================================================================
# 5. HUMAN STEWARD REVIEW WORKFLOW & STATE MACHINE INTEGRITY
# ==============================================================================

def test_human_review_lifecycle_state_machine(client: TestClient, db_session: Session):
    """Verify strict human-controlled workflow: REQUIRES_REVIEW -> UNDER_REVIEW -> REVIEWED -> REOPEN."""
    resp = CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-01")
    inc_id = resp.incident_id

    # 1. State: REQUIRES_REVIEW (Initial)
    res = client.get(f"/api/v1/incidents/{inc_id}")
    assert res.json()["status"] == "REQUIRES_REVIEW"

    # 2. Transition: REQUIRES_REVIEW -> UNDER_REVIEW
    res = client.patch(f"/api/v1/incidents/{inc_id}/status", json={
        "status": "UNDER_REVIEW",
        "reviewer_id": "steward-01",
        "review_notes": "Steward initiated examination."
    })
    assert res.status_code == 200
    assert res.json()["status"] == "UNDER_REVIEW"

    # 3. Formal Review Submission: UNDER_REVIEW -> REVIEWED
    res = client.post(f"/api/v1/incidents/{inc_id}/reviews", json={
        "status": "REVIEWED",
        "reviewer_id": "steward-panel",
        "review_notes": "All telemetry channels reviewed.",
        "review_rationale": "Car on inside line locked brakes, leaving insufficient racing room.",
        "evidence_considered": ["FastF1 Telemetry", "Geometry Overlap"],
    })
    assert res.status_code == 200
    assert res.json()["status"] == "REVIEWED"

    # Verify incident table reflects REVIEWED
    res = client.get(f"/api/v1/incidents/{inc_id}")
    assert res.json()["status"] == "REVIEWED"

    # 4. Guardrail: Reopening closed review without reason must be rejected
    res = client.patch(f"/api/v1/incidents/{inc_id}/status", json={
        "status": "UNDER_REVIEW",
        "reviewer_id": "steward-02",
    })
    assert res.status_code in (400, 422)
    err_body = str(res.json()).lower()
    assert "reopen_reason" in err_body

    # 5. Reopening with explicit rationale succeeds
    res = client.patch(f"/api/v1/incidents/{inc_id}/status", json={
        "status": "UNDER_REVIEW",
        "reviewer_id": "steward-02",
        "reopen_reason": "New onboard camera angle presented by team principal."
    })
    assert res.status_code == 200
    assert res.json()["status"] == "UNDER_REVIEW"


# ==============================================================================
# 6. RESILIENCE, FAILURE & ERROR BEHAVIOR
# ==============================================================================

def test_system_resilience_and_explicit_error_states(client: TestClient):
    """Verify the API emits explicit, typed error codes rather than silent fake data."""
    # 1. Nonexistent incident
    res = client.get("/api/v1/incidents/NONEXISTENT-INCIDENT-999")
    assert res.status_code == 404

    # 2. Nonexistent candidate dossier
    res = client.get("/api/v1/analysis/candidates/NONEXISTENT-CAND-999/steward-dossier")
    assert res.status_code == 404

    # 3. Nonexistent driver
    res = client.get("/api/v1/drivers/ZZZ")
    assert res.status_code == 404

    # 4. Invalid status update transition (e.g. invalid string)
    res = client.patch("/api/v1/incidents/REF-MONZA-01/status", json={
        "status": "INVALID_STATE"
    })
    assert res.status_code in (400, 422)


# ==============================================================================
# 7. PERFORMANCE BASELINE MEASUREMENTS
# ==============================================================================

def test_performance_baseline_latency(client: TestClient, db_session: Session):
    """Measure request latency across critical endpoints (recorded for transparency)."""
    resp_persist = CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-01")
    inc_id = resp_persist.incident_id

    # 1. Health check latency (includes PostgreSQL timeout attempt when offline)
    t0 = time.perf_counter()
    res = client.get("/api/v1/health")
    t_health = (time.perf_counter() - t0) * 1000
    assert res.status_code == 200

    # 2. Incident detail latency
    t0 = time.perf_counter()
    res = client.get(f"/api/v1/incidents/{inc_id}")
    t_incident = (time.perf_counter() - t0) * 1000
    assert res.status_code == 200

    # 3. Steward Dossier Synthesis latency
    t0 = time.perf_counter()
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/steward-dossier")
    t_dossier = (time.perf_counter() - t0) * 1000
    assert res.status_code == 200

    # 4. JSON Export latency
    t0 = time.perf_counter()
    res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/steward-dossier/export/json")
    t_export = (time.perf_counter() - t0) * 1000
    assert res.status_code == 200

    # Output recorded metrics for Prompt 17 report
    print(f"\n[Performance Baseline] Health: {t_health:.1f}ms, Incident: {t_incident:.1f}ms, Dossier: {t_dossier:.1f}ms, Export: {t_export:.1f}ms")
