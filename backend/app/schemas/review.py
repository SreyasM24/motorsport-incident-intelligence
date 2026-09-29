"""Pydantic schemas for human steward review records and candidate persistence."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, computed_field
from pydantic.alias_generators import to_camel


class ReviewStatus(str, Enum):
    """Permitted candidate review lifecycle states."""
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"


class ReviewRecordSchema(BaseModel):
    """Pydantic representation of a human steward review audit entry."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    incident_id: str
    status: ReviewStatus
    reviewer_id: str = Field(default="steward-panel", description="Identifier of human reviewer")
    review_started_at: Optional[datetime] = None
    review_completed_at: Optional[datetime] = None
    evidence_considered: Optional[str] = Field(default=None, description="Summary of evidence channels examined")
    evidence_missing: Optional[str] = Field(default=None, description="Missing or unverified evidence noted")
    observations: Optional[str] = Field(default=None, description="Objective factual observations")
    review_notes: Optional[str] = Field(default=None, description="General reviewer notes")
    review_rationale: Optional[str] = Field(default=None, description="Reasoning for REVIEWED or DISMISSED determination")
    regulatory_references: Optional[str] = Field(default=None, description="Referenced sporting regulations")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReviewCreateRequest(BaseModel):
    """Payload submitted by a human steward when evaluating an incident candidate."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: ReviewStatus = Field(..., description="Target status: UNDER_REVIEW, REVIEWED, DISMISSED, REQUIRES_REVIEW")
    reviewer_id: str = Field(default="steward-panel", description="Steward badge or identifier")
    review_notes: Optional[str] = Field(default=None, description="Observations and commentary")
    review_rationale: Optional[str] = Field(default=None, description="Explicit reason for review outcome")
    evidence_considered: Optional[Union[str, List[str]]] = Field(default=None, description="Evidence reviewed (telemetry, timeline, etc.)")
    evidence_missing: Optional[Union[str, List[str]]] = Field(default=None, description="Any unverified or missing data noted")
    observations: Optional[Union[str, List[str]]] = Field(default=None, description="Specific factual findings")
    regulatory_references: Optional[List[str]] = Field(default=None, description="Applicable regulation codes")
    reopen_reason: Optional[str] = Field(default=None, description="Mandatory rationale when reopening a REVIEWED or DISMISSED case")


class CandidatePersistRequest(BaseModel):
    """Request to persist an algorithmic candidate into the reviewable Incident table."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    candidate_id: str = Field(..., description="Candidate ID from reconstruction engine, e.g. CAND-2024-MON-RIC_HUL-L1-01")
    session_id: Optional[str] = Field(default=None, description="Optional override session ID")
    reviewer_id: str = Field(default="system-ingest", description="Originating identifier")
    initial_notes: Optional[str] = Field(default=None, description="Optional initialization notes")


class CandidatePersistResponse(BaseModel):
    """Result of candidate persistence operation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    incident_id: str
    candidate_id: str
    canonical_fingerprint: str
    status: ReviewStatus
    is_created: bool = Field(..., description="True if new record created, False if already existing (idempotent)")
    created_at: str
    message: str


class BulkCandidatePersistRequest(BaseModel):
    """Bounded batch candidate persistence request."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    season: int = Field(default=2024, ge=2018, le=2030)
    round_or_name: str = Field(default="Italian Grand Prix")
    session: str = Field(default="Race")
    candidate_ids: Optional[List[str]] = Field(default=None, description="Explicit candidate IDs to persist")
    driver_pairs: Optional[List[List[str]]] = Field(default=None, description="Optional driver pairs to reconstruct & persist")
    lap: Optional[int] = Field(default=None, ge=1, le=100)
    limit: int = Field(default=20, ge=1, le=100, description="Max candidates to persist")


class BulkCandidatePersistResponse(BaseModel):
    """Result summary of bulk candidate persistence operation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_requested: int
    created: int
    already_existing: int
    failed: int
    persisted_incidents: List[CandidatePersistResponse]
    execution_time_sec: float

    @computed_field
    @property
    def created_count(self) -> int:
        """Alias for created count."""
        return self.created

    @computed_field
    @property
    def existing_count(self) -> int:
        """Alias for already_existing count."""
        return self.already_existing

    @computed_field
    @property
    def results(self) -> List[CandidatePersistResponse]:
        """Alias for persisted_incidents list."""
        return self.persisted_incidents
