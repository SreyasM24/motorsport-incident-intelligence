"""Candidate domain models, evidence signal representations, and API schemas.

CRITICAL DOCTRINE:
    Candidate events represent objective, sensor-derived interaction episodes requiring
    further human steward or investigator review.
    They do NOT assert guilt, fault, penalty, infringement, or steward outcomes.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class EvidenceSignalType(str, Enum):
    """Categorical classification of empirical evidence signals."""
    SPATIAL_PROXIMITY = "SPATIAL_PROXIMITY"
    KINEMATIC_CLOSING = "KINEMATIC_CLOSING"
    DECELERATION_SPIKE = "DECELERATION_SPIKE"
    VEHICLE_RESPONSE = "VEHICLE_RESPONSE"
    TRAJECTORY_DEVIATION = "TRAJECTORY_DEVIATION"
    RACE_CONTROL_CONTEXT = "RACE_CONTROL_CONTEXT"


class CandidateEventType(str, Enum):
    """Neutral physical classification of candidate interaction events."""
    CONTACT_CANDIDATE = "CONTACT_CANDIDATE"
    RAPID_PROXIMITY_EVENT = "RAPID_PROXIMITY_EVENT"
    SUDDEN_DECELERATION_EVENT = "SUDDEN_DECELERATION_EVENT"
    TRAJECTORY_DEVIATION_EVENT = "TRAJECTORY_DEVIATION_EVENT"
    MULTI_SIGNAL_INTERACTION = "MULTI_SIGNAL_INTERACTION"


class CandidateStatus(str, Enum):
    """Lifecycle status for reconstructed candidate events."""
    PENDING_REVIEW = "PENDING_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    DISMISSED = "DISMISSED"
    CONFIRMED = "CONFIRMED"


class EvidenceSignal(BaseModel):
    """Individual empirical evidence signal detected at a specific timestamp or frame."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    signal_type: EvidenceSignalType
    timestamp: str = Field(..., description="Timestamp string (HH:MM:SS.mmm)")
    time_offset: float = Field(..., description="Elapsed seconds within analysis window")
    observed_value: float = Field(..., description="Quantified numerical value")
    threshold_value: float = Field(..., description="Configured triggering threshold")
    unit: str = Field(..., description="SI or engineering unit (m, m/s, G, %, etc.)")
    description: str = Field(..., description="Objective explanation of observed feature")
    provenance: str = Field(default="telemetry_sync_25hz")


class DataQualityFlags(BaseModel):
    """Data quality and integrity indicators for a candidate episode."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    missing_telemetry: bool = False
    interpolation_heavy: bool = False
    coordinate_discontinuity: bool = False
    different_laps: bool = False
    incomplete_driver_data: bool = False
    race_control_unavailable: bool = False
    low_temporal_coverage: bool = False
    quality_summary: str = "FULL_FIDELITY"


class CandidateDossier(BaseModel):
    """Comprehensive, neutral candidate event dossier for steward investigation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    candidate_id: str
    session_id: str
    event_type: CandidateEventType = CandidateEventType.MULTI_SIGNAL_INTERACTION
    status: CandidateStatus = CandidateStatus.PENDING_REVIEW

    # Temporal bounds
    event_start: str = Field(..., description="Wall-clock or session start time string")
    event_peak: str = Field(..., description="Timestamp of closest proximity / peak interaction")
    event_end: str = Field(..., description="Wall-clock or session end time string")
    duration_seconds: float = Field(..., ge=0.0)

    # Participating drivers
    driver_a: str
    driver_b: str
    lap_number_a: Optional[int] = None
    lap_number_b: Optional[int] = None
    same_lap: bool = True

    # Spatial context
    track_distance_a: Optional[float] = None
    track_distance_b: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    turn: Optional[str] = None

    # Peak empirical dynamics
    minimum_gap_meters: float = Field(..., ge=0.0)
    peak_closing_speed_ms: float
    speed_delta_at_peak: float
    speed_a_at_peak: float
    speed_b_at_peak: float

    # Vehicle responses
    braking_change: Dict[str, Any] = Field(default_factory=dict)
    throttle_change: Dict[str, Any] = Field(default_factory=dict)
    trajectory_change: Dict[str, Any] = Field(default_factory=dict)

    # Supporting contextual evidence
    race_control_context: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_signals: List[EvidenceSignal] = Field(default_factory=list)

    # Evidence strength: 0 to 100 neutral score representing empirical signal convergence.
    # NEVER represents guilt, fault, or penalty probability!
    evidence_strength: int = Field(default=50, ge=0, le=100)

    data_quality_flags: DataQualityFlags = Field(default_factory=DataQualityFlags)
    preprocessing_version: str = "telemetry_preprocessing_v1"
    detection_method: str = "MULTI_SIGNAL_RECONSTRUCTION_V1"
    summary: str = ""


class CandidateQueryRequest(BaseModel):
    """Constrained request payload for candidate extraction."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    season: int = 2024
    round_or_name: str = "Monza"
    session: str = "Race"
    driver_a: Optional[str] = None
    driver_b: Optional[str] = None
    lap: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100, description="Max candidate events returned")


class CandidateBatchResponse(BaseModel):
    """Response containing reconstructed candidate events."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: str
    total_candidates: int
    processing_time_sec: float
    candidates: List[CandidateDossier]
