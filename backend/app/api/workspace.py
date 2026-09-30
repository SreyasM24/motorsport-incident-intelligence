"""API router for Steward Case Workspace, Evidence Triage, and Investigation Review."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.workspace_service import StewardWorkspaceService
from app.schemas.workspace import (
    DiscrepancyStatusUpdateRequest,
    EvidenceAcknowledgementCreateRequest,
    EvidenceAcknowledgementSchema,
    ReviewAuditEntry,
    StewardCaseWorkspace,
    UnresolvedQuestionCreateRequest,
    UnresolvedQuestionSchema,
    UnresolvedQuestionUpdateRequest,
    WorkspaceTimelineEvent,
)

router = APIRouter(prefix="/cases", tags=["Steward Case Workspace & Investigation"])


@router.get(
    "/{candidate_id}/workspace",
    response_model=StewardCaseWorkspace,
    summary="Retrieve canonical Steward Case Workspace read model with evidence triage",
)
def get_case_workspace_endpoint(
    candidate_id: str,
    force_refresh: bool = Query(default=False, description="Bypass cache and regenerate dossier"),
    db: Session = Depends(get_db),
) -> StewardCaseWorkspace:
    """Retrieve unified investigation workspace aggregating telemetry, video, regulations, and review state.

    CRITICAL DOCTRINE:
        Surfaces objective factual evidence, cross-modal discrepancies, and historical comparables
        for human race stewards. It NEVER determines guilt, assigns fault, or recommends penalties.
    """
    try:
        return StewardWorkspaceService.get_workspace(
            candidate_id=candidate_id,
            db=db,
            force_refresh=force_refresh,
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate case '{candidate_id}' not found.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate workspace for '{candidate_id}': {str(e)}",
        )


@router.post(
    "/{candidate_id}/evidence/{evidence_id}/review",
    response_model=EvidenceAcknowledgementSchema,
    summary="Record human steward evidence triage acknowledgement",
)
def record_evidence_acknowledgement_endpoint(
    candidate_id: str,
    evidence_id: str,
    payload: EvidenceAcknowledgementCreateRequest,
    db: Session = Depends(get_db),
) -> EvidenceAcknowledgementSchema:
    """Record that a steward has examined, dismissed, or flagged an evidence item.

    Does NOT modify the underlying evidence or sensor data; records immutable reviewer metadata.
    """
    return StewardWorkspaceService.record_acknowledgement(
        db=db,
        candidate_id=candidate_id,
        evidence_id=evidence_id,
        payload=payload,
    )


@router.post(
    "/{candidate_id}/questions",
    response_model=UnresolvedQuestionSchema,
    summary="Open a structured investigation question for the steward panel",
)
def create_unresolved_question_endpoint(
    candidate_id: str,
    payload: UnresolvedQuestionCreateRequest,
    db: Session = Depends(get_db),
) -> UnresolvedQuestionSchema:
    """Record an open factual or technical question regarding the candidate incident."""
    return StewardWorkspaceService.create_unresolved_question(
        db=db,
        candidate_id=candidate_id,
        payload=payload,
    )


@router.patch(
    "/{candidate_id}/questions/{question_id}",
    response_model=UnresolvedQuestionSchema,
    summary="Update or resolve an open investigation question",
)
def update_unresolved_question_endpoint(
    candidate_id: str,
    question_id: str,
    payload: UnresolvedQuestionUpdateRequest,
    db: Session = Depends(get_db),
) -> UnresolvedQuestionSchema:
    """Update status (OPEN, RESOLVED, DEFERRED) or append notes to an open question."""
    return StewardWorkspaceService.update_unresolved_question(
        db=db,
        candidate_id=candidate_id,
        question_id=question_id,
        payload=payload,
    )


@router.post(
    "/{candidate_id}/discrepancies/{discrepancy_id}/status",
    summary="Update steward inspection status for a cross-modal contradiction",
)
def update_discrepancy_status_endpoint(
    candidate_id: str,
    discrepancy_id: str,
    payload: DiscrepancyStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """Transition discrepancy status (OPEN, ACKNOWLEDGED, RESOLVED, UNRESOLVED)."""
    return StewardWorkspaceService.update_discrepancy_status(
        db=db,
        candidate_id=candidate_id,
        discrepancy_id=discrepancy_id,
        payload=payload,
    )


@router.get(
    "/{candidate_id}/timeline",
    response_model=List[WorkspaceTimelineEvent],
    summary="Retrieve chronological reconstructed incident timeline with uncertainties",
)
def get_case_timeline_endpoint(candidate_id: str) -> List[WorkspaceTimelineEvent]:
    """Retrieve ordered milestone events with explicit sensor uncertainty bounds."""
    try:
        return StewardWorkspaceService.get_timeline(candidate_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate case '{candidate_id}' not found.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve timeline for '{candidate_id}': {str(e)}",
        )


@router.get(
    "/{candidate_id}/audit",
    response_model=List[ReviewAuditEntry],
    summary="Retrieve chronological human steward review audit trail",
)
def get_case_audit_trail_endpoint(
    candidate_id: str,
    db: Session = Depends(get_db),
) -> List[ReviewAuditEntry]:
    """Retrieve complete chronological log of who changed what, when, and why."""
    try:
        return StewardWorkspaceService.get_audit_trail(candidate_id, db=db)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate case '{candidate_id}' not found.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit trail for '{candidate_id}': {str(e)}",
        )
