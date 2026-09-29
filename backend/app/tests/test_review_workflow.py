"""Unit and integration tests for human steward review state machine and workflow."""

import pytest
from sqlalchemy.orm import Session
from app.services.candidate_persistence_service import CandidatePersistenceService
from app.schemas.review import ReviewStatus, ReviewCreateRequest
from app.core.exceptions import ValidationException


def test_valid_state_transitions(db_session: Session):
    """Verify valid progression: REQUIRES_REVIEW -> UNDER_REVIEW -> REVIEWED."""
    resp = CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-01")
    incident_id = resp.incident_id
    assert resp.status == ReviewStatus.REQUIRES_REVIEW

    # Step 1: Begin review -> UNDER_REVIEW
    req_under_review = ReviewCreateRequest(
        status=ReviewStatus.UNDER_REVIEW,
        reviewer_id="steward-1",
        review_notes="Initiated formal inquiry into Turn 1 chicane braking overlap.",
    )
    inc, rev1 = CandidatePersistenceService.transition_status(db_session, incident_id, req_under_review)
    assert inc.status == ReviewStatus.UNDER_REVIEW.value
    assert rev1.review_started_at is not None
    assert rev1.review_completed_at is None
    assert rev1.reviewer_id == "steward-1"

    # Step 2: Mark reviewed -> REVIEWED
    req_reviewed = ReviewCreateRequest(
        status=ReviewStatus.REVIEWED,
        reviewer_id="steward-panel",
        review_notes="Telemetry and video reviewed. Driver overlap established at apex.",
        review_rationale="Article 33.4 satisfied; normal racing room maintained.",
    )
    inc, rev2 = CandidatePersistenceService.transition_status(db_session, incident_id, req_reviewed)
    assert inc.status == ReviewStatus.REVIEWED.value
    assert rev2.review_completed_at is not None
    assert rev2.review_rationale == "Article 33.4 satisfied; normal racing room maintained."

    # Audit history should show 3 records: initial + under_review + reviewed
    reviews = CandidatePersistenceService.get_incident_reviews(db_session, incident_id)
    assert len(reviews) == 3
    assert reviews[-1].status == ReviewStatus.REVIEWED.value


def test_invalid_transition_direct_to_reviewed(db_session: Session):
    """Verify direct jump from REQUIRES_REVIEW -> REVIEWED is strictly prohibited."""
    resp = CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-02")
    incident_id = resp.incident_id

    req_illegal = ReviewCreateRequest(
        status=ReviewStatus.REVIEWED,
        reviewer_id="steward-1",
        review_notes="Attempting to skip under review.",
    )
    with pytest.raises(ValidationException) as exc_info:
        CandidatePersistenceService.transition_status(db_session, incident_id, req_illegal)
    assert "Invalid transition" in str(exc_info.value.message)


def test_invalid_terminal_to_terminal(db_session: Session):
    """Verify terminal to terminal transition (REVIEWED -> DISMISSED) is prohibited."""
    resp = CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-03")
    incident_id = resp.incident_id
    
    # Progress to UNDER_REVIEW then REVIEWED
    CandidatePersistenceService.transition_status(
        db_session,
        incident_id,
        ReviewCreateRequest(status=ReviewStatus.UNDER_REVIEW),
    )
    CandidatePersistenceService.transition_status(
        db_session,
        incident_id,
        ReviewCreateRequest(status=ReviewStatus.REVIEWED),
    )

    # Attempt to dismiss directly from REVIEWED
    with pytest.raises(ValidationException):
        CandidatePersistenceService.transition_status(
            db_session,
            incident_id,
            ReviewCreateRequest(status=ReviewStatus.DISMISSED),
        )


def test_reopen_requires_reason(db_session: Session):
    """Verify reopening from terminal state requires an explicit reopen reason."""
    resp = CandidatePersistenceService.persist_by_candidate_id(db_session, "REF-MONZA-01")
    incident_id = resp.incident_id
    
    # Progress to UNDER_REVIEW then DISMISSED
    CandidatePersistenceService.transition_status(
        db_session,
        incident_id,
        ReviewCreateRequest(status=ReviewStatus.UNDER_REVIEW),
    )
    CandidatePersistenceService.transition_status(
        db_session,
        incident_id,
        ReviewCreateRequest(status=ReviewStatus.DISMISSED, review_rationale="No further action needed."),
    )

    # Reopening without reason should fail
    with pytest.raises(ValidationException) as exc:
        CandidatePersistenceService.transition_status(
            db_session,
            incident_id,
            ReviewCreateRequest(status=ReviewStatus.UNDER_REVIEW, reopen_reason=""),
        )
    assert "reopen_reason" in str(exc.value.message)

    # Reopening with non-empty reason should succeed
    inc, rev = CandidatePersistenceService.transition_status(
        db_session,
        incident_id,
        ReviewCreateRequest(
            status=ReviewStatus.UNDER_REVIEW,
            reopen_reason="New onboard 360-degree footage provided by competitor team.",
        ),
    )
    assert inc.status == ReviewStatus.UNDER_REVIEW.value
    assert "New onboard" in rev.observations
    assert "New onboard" in rev.review_rationale


def test_api_review_lifecycle_endpoints(client):
    """Verify PATCH /api/v1/incidents/{id}/status and GET /api/v1/incidents/{id}/reviews."""
    # Persist candidate
    res_p = client.post("/api/v1/analysis/candidates/persist", json={"candidate_id": "REF-MONZA-01"})
    assert res_p.status_code == 200
    incident_id = res_p.json()["incidentId"]

    # 1. Begin Review
    res_under = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "UNDER_REVIEW", "reviewer_id": "steward-panel", "review_notes": "Starting review"},
    )
    assert res_under.status_code == 200
    assert res_under.json()["status"] == "UNDER_REVIEW"

    # 2. Check reviews audit history
    res_audit = client.get(f"/api/v1/incidents/{incident_id}/reviews")
    assert res_audit.status_code == 200
    reviews = res_audit.json()
    assert len(reviews) == 2
    assert reviews[-1]["status"] == "UNDER_REVIEW"

    # 3. Post formal review submission
    res_post_rev = client.post(
        f"/api/v1/incidents/{incident_id}/reviews",
        json={
            "status": "REVIEWED",
            "reviewer_id": "steward-chief",
            "review_notes": "Full session analysis complete.",
            "review_rationale": "Racing incident; both drivers had partial room.",
            "evidence_considered": ["Telemetry", "Video"],
            "evidence_missing": ["Micro-strain gauges"],
            "observations": ["Apex speed delta +4km/h"],
            "regulatory_references": ["Article 33.4"],
        },
    )
    assert res_post_rev.status_code == 200
    rev_data = res_post_rev.json()
    assert rev_data["status"] == "REVIEWED"
    assert rev_data["reviewCompletedAt"] is not None

    # 4. Confirm incident status is now REVIEWED
    res_get = client.get(f"/api/v1/incidents/{incident_id}")
    assert res_get.status_code == 200
    assert res_get.json()["status"] == "REVIEWED"
