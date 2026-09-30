"""Pydantic schemas and contracts for the Steward Case Workspace.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS:
    1. Zero Autonomous Guilt or Fault Determination: The workspace presents
       structured, multi-modal evidence for human steward investigation.
    2. Zero Penalty Recommendation: The system never proposes penalties,
       fault splits, or regulatory liability.
    3. Epistemic Separation: Distinguishes OBSERVED, DERIVED, MODEL_DERIVED,
       DOCUMENTARY, and UNAVAILABLE evidence.
    4. Deterministic Triage: Ordering is an investigation UX tool, never proof of fault.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


# ==============================================================================
# 1. ENUMS
# ==============================================================================

class TriageEpistemicType(str, Enum):
    """Explicit epistemic categorization of evidence items."""
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    MODEL_DERIVED = "MODEL_DERIVED"
    DOCUMENTARY = "DOCUMENTARY"
    UNAVAILABLE = "UNAVAILABLE"


class TriageAvailability(str, Enum):
    """Rigorous availability rating without zero-imputation distortion."""
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    LIMITED = "LIMITED"
    UNAVAILABLE = "UNAVAILABLE"


class AcknowledgementAction(str, Enum):
    """Human steward review actions applied to individual evidence items."""
    CONSIDERED = "CONSIDERED"
    NOT_RELEVANT = "NOT_RELEVANT"
    INSUFFICIENT = "INSUFFICIENT"
    CONTRADICTORY = "CONTRADICTORY"
    REQUIRES_FOLLOW_UP = "REQUIRES_FOLLOW_UP"


class QuestionStatus(str, Enum):
    """Status of an unresolved steward investigation question."""
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DEFERRED = "DEFERRED"


class DiscrepancyStatus(str, Enum):
    """Status of cross-modal evidence discrepancy review."""
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


# ==============================================================================
# 2. EVIDENCE ACKNOWLEDGEMENT SCHEMAS
# ==============================================================================

class EvidenceAcknowledgementSchema(BaseModel):
    """Read model for a reviewer's evidence item acknowledgement."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    candidate_id: str
    evidence_id: str
    reviewer_id: str
    action: AcknowledgementAction
    note: Optional[str] = None
    created_at: datetime


class EvidenceAcknowledgementCreateRequest(BaseModel):
    """Payload to record an evidence triage acknowledgement."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    reviewer_id: str = Field(default="steward-panel", description="Identifier of human steward")
    action: AcknowledgementAction = Field(..., description="Triage action applied to evidence item")
    note: Optional[str] = Field(default=None, description="Optional steward rationale or observation")


# ==============================================================================
# 3. UNRESOLVED QUESTION SCHEMAS
# ==============================================================================

class UnresolvedQuestionSchema(BaseModel):
    """Read model for a steward's unresolved investigation question."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    candidate_id: str
    question: str
    evidence_ids: List[str] = Field(default_factory=list)
    status: QuestionStatus = QuestionStatus.OPEN
    reviewer_note: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class UnresolvedQuestionCreateRequest(BaseModel):
    """Payload to open an unresolved investigation question."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    question: str = Field(..., description="The factual or technical uncertainty to resolve")
    evidence_ids: Optional[List[str]] = Field(default=None, description="Related evidence IDs")
    reviewer_note: Optional[str] = Field(default=None, description="Contextual investigation note")


class UnresolvedQuestionUpdateRequest(BaseModel):
    """Payload to update or resolve an open question."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: Optional[QuestionStatus] = Field(default=None, description="Updated status: OPEN, RESOLVED, DEFERRED")
    reviewer_note: Optional[str] = Field(default=None, description="Resolution rationale or findings")


class DiscrepancyStatusUpdateRequest(BaseModel):
    """Payload to transition discrepancy review status."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: DiscrepancyStatus = Field(..., description="Target status: OPEN, ACKNOWLEDGED, RESOLVED, UNRESOLVED")
    reviewer_id: str = Field(default="steward-panel")
    note: Optional[str] = Field(default=None, description="Steward observation regarding the contradiction")


# ==============================================================================
# 4. WORKSPACE CASE INFO & EVIDENCE STREAM SUMMARIES
# ==============================================================================

class WorkspaceCaseInfo(BaseModel):
    """Core case identifiers and participants for workspace header."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    candidate_id: str
    incident_id: Optional[str] = None
    session: str
    event: str
    circuit: str
    timestamp: str
    drivers: List[str]
    incident_status: str
    review_status: str
    analysis_version: str = "v1.0"


class WorkspaceIncidentSummary(BaseModel):
    """Kinematic detection and geometric location summary."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    incident_type: str
    detection_method: str
    confidence: int = Field(..., description="Sensor correlation confidence 0-100; NOT guilt or liability")
    timeline_window: str
    track_position: Optional[str] = None
    lap_number: int


class WorkspaceEvidenceStreamSummary(BaseModel):
    """Per-stream availability, epistemic type, and limitations summary."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    availability: TriageAvailability
    epistemic_type: TriageEpistemicType
    quality: str
    provenance: str
    timestamp_coverage: str
    limitations: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)


# ==============================================================================
# 5. EVIDENCE TRIAGE ITEM & TIMELINE SCHEMAS
# ==============================================================================

class WorkspaceEvidenceItem(BaseModel):
    """An inspectable individual evidence item with deterministic triage metadata."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evidence_id: str
    evidence_type: str
    epistemic_type: TriageEpistemicType
    source: str
    availability: TriageAvailability
    quality: str
    timestamp: Optional[str] = None
    relevance: str
    provenance: str
    limitations: List[str] = Field(default_factory=list)
    discrepancy_status: str = "NONE"
    observation: str
    value: Optional[Any] = None
    unit: Optional[str] = None
    parent_evidence_ids: List[str] = Field(default_factory=list)
    triage_priority: int = Field(
        ...,
        description="Deterministic UX ordering: 1=OBSERVED, 2=DERIVED, 3=MODEL_DERIVED, 4=DOCUMENTARY, 5=UNAVAILABLE",
    )
    latest_acknowledgement: Optional[EvidenceAcknowledgementSchema] = None


class WorkspaceTimelineEvent(BaseModel):
    """A chronologically reconstructed event milestone in the candidate window."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    timestamp: str
    event_relative_time_sec: float
    source: str
    epistemic_type: TriageEpistemicType
    description: str
    measurement: Optional[str] = None
    uncertainty: Optional[str] = None
    provenance: str
    evidence_ref: Optional[str] = None


class WorkspaceDiscrepancyItem(BaseModel):
    """Active cross-modal contradiction or alignment issue surfaced to stewards."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    discrepancy_id: str
    evidence_a: str
    evidence_b: str
    discrepancy_type: str
    magnitude: str
    uncertainty: str
    explanation: str
    severity: str
    status: DiscrepancyStatus = DiscrepancyStatus.OPEN
    affected_evidence_ids: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class ReviewAuditEntry(BaseModel):
    """Historical human review state transition entry."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    status: str
    reviewer_id: str
    timestamp: str
    notes: Optional[str] = None
    rationale: Optional[str] = None
    evidence_considered: Optional[str] = None
    evidence_missing: Optional[str] = None
    observations: Optional[str] = None


class WorkspaceReviewSummary(BaseModel):
    """Complete human steward evaluation state, open questions, and audit trail."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    current_state: str
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    review_rationale: Optional[str] = None
    evidence_acknowledgements: List[EvidenceAcknowledgementSchema] = Field(default_factory=list)
    unresolved_questions: List[UnresolvedQuestionSchema] = Field(default_factory=list)
    review_history: List[ReviewAuditEntry] = Field(default_factory=list)


# ==============================================================================
# 6. CANONICAL STEWARD CASE WORKSPACE READ MODEL
# ==============================================================================

class StewardCaseWorkspace(BaseModel):
    """The canonical read model aggregating all evidence subsystems for steward investigation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    case: WorkspaceCaseInfo
    incident_summary: WorkspaceIncidentSummary
    evidence_summary: Dict[str, WorkspaceEvidenceStreamSummary]
    evidence_items: List[WorkspaceEvidenceItem] = Field(default_factory=list)
    timeline: List[WorkspaceTimelineEvent] = Field(default_factory=list)
    discrepancies: List[WorkspaceDiscrepancyItem] = Field(default_factory=list)
    historical_comparables: Optional[Any] = None
    regulations: List[Any] = Field(default_factory=list)
    review: WorkspaceReviewSummary
    doctrine: str = (
        "CRITICAL STEWARD DOCTRINE: This workspace organizes empirical, kinematic, and documentary evidence "
        "to assist human race stewards. It strictly DOES NOT automate driver guilt, assign fault probabilities, "
        "issue penalties, or make legal adjudications. Human stewards retain exclusive decision authority."
    )
