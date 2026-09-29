"""Pydantic schemas and models for Cornering Overtake Geometry & Apex Overlap Analysis.

CRITICAL JURISPRUDENTIAL GUARDRAILS:
    This module produces MEASURABLE GEOMETRIC EVIDENCE ONLY.
    It DOES NOT decide fault, guilt, penalty, legality, or which driver was responsible.
    All outputs represent objective physical quantities for human steward deliberation.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class MeasurementConfidence(str, Enum):
    """Integrity and provenance classification of geometric calculations."""
    DIRECTLY_OBSERVED = "DIRECTLY_OBSERVED"
    DERIVED_FROM_TELEMETRY = "DERIVED_FROM_TELEMETRY"
    DERIVED_FROM_POSITION = "DERIVED_FROM_POSITION"
    PARTIALLY_OBSERVABLE = "PARTIALLY_OBSERVABLE"
    UNAVAILABLE = "UNAVAILABLE"


class RelativeLongitudinalPosition(str, Enum):
    """Purely measured physical ordering along the track distance axis."""
    AHEAD = "AHEAD"
    BEHIND = "BEHIND"
    APPROXIMATELY_ALONGSIDE = "APPROXIMATELY_ALONGSIDE"
    UNAVAILABLE = "UNAVAILABLE"


class OverlapClassification(str, Enum):
    """Geometric longitudinal overlap classification relative to vehicle reference length."""
    NO_MEASURABLE_OVERLAP = "NO_MEASURABLE_OVERLAP"
    PARTIAL_OVERLAP = "PARTIAL_OVERLAP"
    APPROXIMATELY_50_PERCENT_OVERLAP = "APPROXIMATELY_50_PERCENT_OVERLAP"
    GREATER_THAN_50_PERCENT_OVERLAP = "GREATER_THAN_50_PERCENT_OVERLAP"
    OVERLAP_ANALYSIS_LIMITED = "OVERLAP_ANALYSIS_LIMITED"
    INSUFFICIENT_GEOMETRIC_DATA = "INSUFFICIENT_GEOMETRIC_DATA"


class ExitClearanceClassification(str, Enum):
    """Objective spatial clearance categorization relative to the 2.0m car width reference."""
    CLEARANCE_ABOVE_REFERENCE = "CLEARANCE_ABOVE_REFERENCE"
    CLEARANCE_NEAR_REFERENCE = "CLEARANCE_NEAR_REFERENCE"
    CLEARANCE_BELOW_REFERENCE = "CLEARANCE_BELOW_REFERENCE"
    CLEARANCE_UNAVAILABLE = "CLEARANCE_UNAVAILABLE"


class CornerPhaseSnapshot(BaseModel):
    """Spatial and kinematic state of both vehicles at a specific corner milestone."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    phase_name: str = Field(..., description="ENTRY, BRAKING_ONSET, TURN_IN, APEX, APEX_PLUS_10M, APEX_PLUS_20M, EXIT")
    distance_incident_m: float
    distance_other_m: float
    delta_s_m: float = Field(..., description="s_incident - s_other (m). Positive = incident car ahead.")
    delta_t_sec: Optional[float] = Field(default=None, description="t_incident - t_other at matching distance (s)")

    speed_incident_kmh: float
    speed_other_kmh: float
    speed_delta_kmh: float

    lateral_gap_m: Optional[float] = None
    euclidean_gap_m: Optional[float] = None
    relative_position: RelativeLongitudinalPosition = RelativeLongitudinalPosition.APPROXIMATELY_ALONGSIDE

    confidence: MeasurementConfidence = MeasurementConfidence.DERIVED_FROM_POSITION


class ApexOverlapSnapshot(BaseModel):
    """Dedicated apex frame snapshot quantifying spatial and kinematic relationship."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    incident_car_code: str
    incident_distance_m: float
    incident_speed_kmh: float
    incident_x_m: Optional[float] = None
    incident_y_m: Optional[float] = None

    other_car_code: str
    other_distance_m: float
    other_speed_kmh: float
    other_x_m: Optional[float] = None
    other_y_m: Optional[float] = None

    longitudinal_gap_m: float = Field(..., description="s_incident - s_other (m)")
    lateral_gap_m: Optional[float] = Field(default=None, description="Approximate cross-track lateral separation (m)")
    euclidean_gap_m: Optional[float] = Field(default=None, description="2D Cartesian distance between vehicle positions (m)")

    relative_position: RelativeLongitudinalPosition
    overlap_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Measured longitudinal overlap (%)")
    overlap_classification: OverlapClassification = OverlapClassification.INSUFFICIENT_GEOMETRIC_DATA

    front_axle_gap_m: Optional[float] = None
    mirror_reference_overlap_percent: Optional[float] = None

    confidence: MeasurementConfidence = MeasurementConfidence.DERIVED_FROM_POSITION


class CornerPhases(BaseModel):
    """Deterministic boundaries of the cornering episode."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    corner_entry_distance_m: float
    corner_entry_time_s: float
    entry_detection_method: str = "LONGITUDINAL_DECELERATION_THRESHOLD"

    apex_distance_m: float
    apex_time_s: float
    apex_speed_kmh: float
    apex_detection_method: str = "MINIMUM_CORNER_SPEED"

    corner_exit_distance_m: Optional[float] = None
    corner_exit_time_s: Optional[float] = None
    exit_detection_status: str = "AVAILABLE"  # AVAILABLE or UNAVAILABLE
    exit_detection_method: Optional[str] = "THROTTLE_REAPPLICATION_AND_ACCELERATION"


class ExitClearanceMetrics(BaseModel):
    """Spatial clearance assessment at corner exit relative to the 2.0m reference width."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    exit_distance_m: Optional[float] = None
    measured_clearance_m: Optional[float] = None
    reference_width_threshold_m: float = 2.00
    reference_width_source: str = "FIA Formula One Technical Regulations 2024, Article 3.3 (2000mm max width)"
    clearance_classification: ExitClearanceClassification = ExitClearanceClassification.CLEARANCE_UNAVAILABLE
    confidence: MeasurementConfidence = MeasurementConfidence.DERIVED_FROM_POSITION
    note: str = Field(
        default="Measured clearance is evaluated against the 2.00m vehicle width mandated by FIA F1 Technical Regulations Article 3.3. "
        "This is an empirical physical measurement, not a fault determination."
    )


class FIAGuidelineReference(BaseModel):
    """External normative reference metadata for driving standards guidance."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    rule_source: str = "FIA Formula One Driving Standards Guidelines"
    rule_reference: str = "Section 2: Overtaking (Inside/Outside at Corner Apex)"
    rule_version_or_date: str = "2024 Edition"
    measurement_definition: str = (
        "Evaluation of whether the overtaking car has a significant portion alongside (front axle alongside mirror or front axle to front axle) at corner apex."
    )
    threshold: str = "50% overlap (front axle to front axle / alongside mirror) and 2.0m exit room"
    threshold_type: str = "ENGINEERING_AND_REGULATORY_REFERENCE"
    length_reference_provenance: str = "ENGINEERING_REFERENCE (Derived modern F1 vehicle envelope: 5.63m)"
    width_reference_provenance: str = "FIA_TECHNICAL_REGULATION (FIA 2024 F1 Technical Regulations Article 3.3: 2000mm overall car width)"
    guidelines_standard_provenance: str = "FIA_DRIVING_STANDARDS_GUIDELINES (Qualitative stewarding standard; metric thresholds are engineering approximations)"
    steward_discretion_statement: str = (
        "Official FIA Driving Standards Guidelines serve as guidance for race stewards. "
        "The system quantifies empirical geometric deltas; it does not issue automated penalties or adjudications."
    )


class OvertakeGeometryDataQuality(BaseModel):
    """Quality and sensor integrity indicators for overtake geometry analysis."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    synchronized_timestamps: bool = True
    distance_monotonic: bool = True
    missing_telemetry: bool = False
    unrealistic_positional_jumps: bool = False
    vehicle_dimension_assumptions_used: bool = False
    limitations: List[str] = Field(default_factory=list)


class OvertakeGeometryEvidence(BaseModel):
    """Master structured payload for cornering overtake geometry and apex overlap evidence."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    incident_id: str
    driver_incident: str
    driver_other: str
    turn: str = "Corner"

    corner_phases: CornerPhases
    apex_snapshot: ApexOverlapSnapshot
    exit_clearance: ExitClearanceMetrics
    phase_snapshots: List[CornerPhaseSnapshot] = Field(default_factory=list)

    overlap_classification: OverlapClassification
    overlap_percent: Optional[float] = None
    front_axle_overlap_ratio: Optional[float] = None
    front_axle_overlap_percent: Optional[float] = None

    fia_reference: FIAGuidelineReference = Field(default_factory=FIAGuidelineReference)
    data_quality: OvertakeGeometryDataQuality = Field(default_factory=OvertakeGeometryDataQuality)
    provenance_summary: Dict[str, MeasurementConfidence] = Field(default_factory=dict)
    summary: str = ""
    steward_guidance: str = Field(
        default="Overtake geometry and overlap metrics quantify the relative positions and spatial room afforded "
        "at corner entry, apex, and exit under physical trajectory measurements. These factual quantities "
        "inform human steward review and DO NOT constitute an automated determination of guilt, fault, or legality."
    )
