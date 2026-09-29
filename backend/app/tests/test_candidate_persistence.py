"""Unit and integration tests for candidate persistence and idempotency."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.incident import Incident
from app.models.incident_driver import IncidentDriver
from app.models.review import ReviewRecord
from app.services.candidate_persistence_service import CandidatePersistenceService
from app.schemas.review import ReviewStatus


def test_persist_monza_reference_candidates(db_session: Session):
    """Verify persisting the 3 Monza reference candidates succeeds with correct attributes."""
    expected_meta = {
        "REF-MONZA-01": {"drivers": {"RIC", "HUL"}, "lap": 1},
        "REF-MONZA-02": {"drivers": {"HUL", "TSU"}, "lap": 4},
        "REF-MONZA-03": {"drivers": {"MAG", "GAS"}, "lap": 19},
    }
    
    for ref_id, exp in expected_meta.items():
        resp = CandidatePersistenceService.persist_by_candidate_id(db_session, ref_id)
        assert resp is not None
        assert resp.is_created is True
        assert resp.status == ReviewStatus.REQUIRES_REVIEW
        assert resp.canonical_fingerprint.startswith("MII::")

        incident = db_session.get(Incident, resp.incident_id)
        assert incident is not None
        assert incident.status == ReviewStatus.REQUIRES_REVIEW.value
        assert incident.candidate_id is not None
        assert incident.lap == exp["lap"]
        assert incident.data_quality_summary is not None
        assert incident.dossier_data is not None

        # Verify involved drivers exist and have neutral roles
        drivers = incident.drivers_involved
        assert len(drivers) == 2
        driver_codes = {d.driver.code for d in drivers if d.driver}
        assert driver_codes == exp["drivers"]
        for d in drivers:
            assert d.role in ("PRIMARY", "SECONDARY")
            assert d.role not in ("GUILTY", "AT_FAULT", "CULPRIT", "PENALIZED")

        # Verify initial review record exists
        initial_reviews = incident.reviews
        assert len(initial_reviews) >= 1
        assert initial_reviews[0].status == ReviewStatus.REQUIRES_REVIEW.value
        assert initial_reviews[0].reviewer_id == "system-ingest"



def test_candidate_persistence_idempotency(db_session: Session):
    """Verify persisting the exact same candidate multiple times does NOT create duplicates."""
    ref_id = "REF-MONZA-01"
    
    # First persistence
    resp1 = CandidatePersistenceService.persist_by_candidate_id(db_session, ref_id)
    assert resp1.is_created is True
    initial_id = resp1.incident_id

    # Second persistence of the exact same candidate
    resp2 = CandidatePersistenceService.persist_by_candidate_id(db_session, ref_id)
    assert resp2.is_created is False
    assert resp2.incident_id == initial_id

    # Third persistence
    resp3 = CandidatePersistenceService.persist_by_candidate_id(db_session, ref_id)
    assert resp3.is_created is False
    assert resp3.incident_id == initial_id

    # Verify database total count
    all_incidents = db_session.scalars(select(Incident).where(Incident.canonical_fingerprint == resp1.canonical_fingerprint)).all()
    assert len(all_incidents) == 1


def test_persist_candidate_neutral_roles(db_session: Session):
    """Verify driver associations strictly preserve neutrality without assessing blame."""
    resp = CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-02")
    incident = db_session.get(Incident, resp.incident_id)
    driver_roles = [d.role for d in incident.drivers_involved]
    assert "PRIMARY" in driver_roles
    assert "SECONDARY" in driver_roles
    assert "GUILTY" not in driver_roles
    assert "PENALIZED" not in driver_roles


def test_api_persist_single_candidate(client):
    """Verify POST /api/v1/analysis/candidates/persist endpoint."""
    response = client.post(
        "/api/v1/analysis/candidates/persist",
        json={"candidate_id": "REF-MONZA-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["isCreated"] is True
    assert data["status"] == "REQUIRES_REVIEW"
    assert "incidentId" in data

    # Re-persisting should report isCreated: false
    response2 = client.post(
        "/api/v1/analysis/candidates/persist",
        json={"candidate_id": "REF-MONZA-01"},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["isCreated"] is False


def test_api_persist_batch_candidates(client):
    """Verify POST /api/v1/analysis/candidates/persist-batch endpoint."""
    response = client.post(
        "/api/v1/analysis/candidates/persist-batch",
        json={"candidate_ids": ["REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["totalRequested"] == 3
    assert data["created"] == 3
    assert data["createdCount"] == 3
    assert len(data["persistedIncidents"]) == 3
    assert len(data["results"]) == 3
    for res in data["persistedIncidents"]:
        assert res["isCreated"] is True
        assert "incidentId" in res

    # Re-batch should report 0 created
    response2 = client.post(
        "/api/v1/analysis/candidates/persist-batch",
        json={"candidate_ids": ["REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"]},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["created"] == 0
    assert data2["createdCount"] == 0
    assert data2["alreadyExisting"] == 3
    assert data2["existingCount"] == 3

