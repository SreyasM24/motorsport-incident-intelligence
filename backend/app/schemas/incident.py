"""Pydantic schemas for Incident candidates and evidence assessments."""

from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from app.schemas.baseline import BaselineEvidence
from app.schemas.overtake_geometry import OvertakeGeometryEvidence
from app.schemas.ml_evidence import MLEvidence
from app.schemas.video_evidence import VideoEvidenceSummary
from app.schemas.regulation import RelevantRegulationSchema, EvidenceRegulationConnectionSchema


class TimeWindow(BaseModel):
    """Start and end bounds of an incident telemetry window."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    start: str = Field(..., description="Start timestamp string, e.g. 13:42:16.0")
    end: str = Field(..., description="End timestamp string, e.g. 13:42:21.0")


class EvidenceSources(BaseModel):
    """Data source provenance descriptions for evidence items."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    telemetry: str = "FastF1 ECU CAN-Bus + GPS 25Hz"
    video: str = "World Feed T4 (Pending Sync)"
    regulations: str = "FIA Formula One Sporting Regulations 2024"


class EvidenceItemSchema(BaseModel):
    """Quantified empirical observation for an incident candidate."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    category: str = Field(..., description="PROXIMITY, RELATIVE_MOTION, VEHICLE_RESPONSE, TRAJECTORY, BRAKING")
    title: str
    observed_value: str
    expected_context: str
    confidence: int = Field(..., ge=0, le=100, description="Measurement reliability score (0-100)")
    source: str
    description: str
    verified: bool = True


class IncidentTimelineMilestoneSchema(BaseModel):
    """Chronological event marker within the incident sequence."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    timestamp: str
    label: str
    description: str
    icon_type: str = Field(default="approach", description="approach, proximity, contact, motion, response, exit")
    evidence_ref: Optional[str] = None


class IncidentSummary(BaseModel):
    """Lightweight summary model for Incident Explorer tables and search results."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    session: str
    race_id: str
    circuit: str
    lap: int
    turn: str
    timestamp: str
    driver_a: str
    driver_b: str
    incident_type: str
    confidence: int = Field(..., ge=0, le=100, description="Algorithmic correlation confidence score")
    status: str = Field(default="REQUIRES_REVIEW", description="REQUIRES_REVIEW, UNDER_REVIEW, REVIEWED, DETECTED")
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")


class IncidentDetailResponse(BaseModel):
    """Full 8-part incident evidence dossier for human steward review."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    session: str
    race_id: str
    circuit: str
    lap: int
    turn: str
    timestamp: str
    time_window: TimeWindow
    driver_a: str
    driver_b: str
    incident_type: str
    confidence: int = Field(..., ge=0, le=100, description="Correlation confidence metric")
    status: str
    severity: str
    summary: str
    detection_method: str
    video_available: bool = False
    video_path: Optional[str] = None
    telemetry_available: bool = True
    regulations_available: bool = True
    sources: EvidenceSources = Field(default_factory=EvidenceSources)
    evidence_assessment: List[EvidenceItemSchema] = Field(default_factory=list)
    relevant_regulations: List[RelevantRegulationSchema] = Field(default_factory=list)
    evidence_connections: List[EvidenceRegulationConnectionSchema] = Field(default_factory=list)
    timeline: List[IncidentTimelineMilestoneSchema] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    baseline_evidence: Optional[BaselineEvidence] = None
    overtake_geometry: Optional[OvertakeGeometryEvidence] = None
    ml_evidence: Optional[MLEvidence] = None
    video_evidence: Optional[VideoEvidenceSummary] = None
    visual_evidence: Optional[Any] = None


class IncidentListResponse(BaseModel):
    """Collection wrapper for incident queries."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: List[IncidentSummary]
    total: int


from app.schemas.review import ReviewStatus


class IncidentStatusUpdate(BaseModel):
    """Request payload for updating steward review status."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: ReviewStatus = Field(
        ...,
        description="Updated status: UNDER_REVIEW, REVIEWED, DISMISSED, or REQUIRES_REVIEW",
    )
    reviewer_id: Optional[str] = Field(default="steward-panel", description="Steward identifier")
    review_notes: Optional[str] = Field(default=None, description="Human reviewer observational notes")
    review_rationale: Optional[str] = Field(default=None, description="Reasoning for decision")
    reopen_reason: Optional[str] = Field(default=None, description="Reason if reopening case")
