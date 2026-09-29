"""Reference-Lap Baseline and Incident Evidence Quantification Pydantic schemas.

CRITICAL JURISPRUDENTIAL DOCTRINE:
    Reference-lap baselines quantify physical deviations from representative nominal
    racing conditions for the same driver, car, and session.
    Deviations indicate physical disturbance, avoidance maneuvers, or alternative
    racing lines; they DO NOT prove fault, guilt, intent, or steward decisions.
    
SIGNAL FIDELITY DOCTRINE:
    - OBSERVED: Directly measured by calibrated vehicle sensors (speed, throttle, brake flag/pct, gear, rpm).
    - DERIVED: Empirically calculated from observed signals (longitudinal accel, Euclidean trajectory deviation).
    - UNAVAILABLE: Explicitly flagged when sensor or channel does not exist (steering angle, brake line pressure,
      track-relative curvilinear coordinates).
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SignalStatus(str, Enum):
    """Integrity and provenance classification of telemetry and kinematic channels."""
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    UNAVAILABLE = "UNAVAILABLE"


class BaselineStatus(str, Enum):
    """Operational status of the reference lap baseline computation."""
    AVAILABLE = "AVAILABLE"
    INSUFFICIENT_REFERENCE_DATA = "INSUFFICIENT_REFERENCE_DATA"
    ALIGNMENT_FAILED = "ALIGNMENT_FAILED"


class BaselineDisruptionMetrics(BaseModel):
    """Empirical quantification of driver input disruptions against nominal baseline."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    driver_code: str
    
    # Braking onset kinematics (negative = earlier braking, positive = later braking)
    braking_onset_delta_m: Optional[float] = Field(
        default=None,
        description="Distance difference (m) between incident brake application and baseline nominal braking point"
    )
    braking_onset_delta_sec: Optional[float] = Field(
        default=None,
        description="Temporal difference (s) between incident brake application and baseline nominal braking point"
    )
    peak_brake_pct_delta: Optional[float] = Field(
        default=None,
        description="Peak brake application disparity (%) compared to nominal baseline"
    )

    # Throttle modulation
    throttle_lift_delta_m: Optional[float] = Field(
        default=None,
        description="Distance offset (m) where driver lifted off full throttle relative to baseline"
    )
    throttle_reapplication_delay_m: Optional[float] = Field(
        default=None,
        description="Distance delay (m) from apex to post-corner throttle reapplication (>50%) relative to baseline"
    )
    throttle_reapplication_delay_sec: Optional[float] = Field(
        default=None,
        description="Temporal delay (s) from apex to post-corner throttle reapplication relative to baseline"
    )

    # Apex dynamics
    min_corner_speed_delta_kmh: Optional[float] = Field(
        default=None,
        description="Incident minimum corner speed minus baseline nominal minimum corner speed (km/h)"
    )
    speed_at_apex_incident_kmh: Optional[float] = Field(
        default=None,
        description="Incident vehicle speed (km/h) at the minimum speed corner apex"
    )
    speed_at_apex_baseline_kmh: Optional[float] = Field(
        default=None,
        description="Nominal baseline vehicle speed (km/h) at the minimum speed corner apex"
    )


class TrajectoryDeviationMetrics(BaseModel):
    """Planar trajectory deviation metrics relative to the median reference line."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    driver_code: str
    status: SignalStatus = SignalStatus.DERIVED
    
    max_trajectory_deviation_m: float = Field(
        ...,
        ge=0.0,
        description="Maximum Euclidean distance (m) between incident path and median reference baseline"
    )
    mean_trajectory_deviation_m: float = Field(
        ...,
        ge=0.0,
        description="Mean Euclidean distance (m) between incident path and median reference baseline across window"
    )
    deviation_at_apex_m: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Euclidean distance (m) between incident path and median baseline at corner apex"
    )
    lateral_track_deviation_status: SignalStatus = Field(
        default=SignalStatus.UNAVAILABLE,
        description="Track-relative curvilinear coordinate (d) is unavailable in standard telemetry"
    )
    note: str = Field(
        default="Trajectory deviation is computed via 2D Cartesian Euclidean distance (X, Y in SI meters). "
        "Curvilinear track-relative lateral coordinate (d) is UNAVAILABLE in standard FastF1 telemetry."
    )


class SignalProvenanceInfo(BaseModel):
    """Explicit catalog of signal availability and provenance."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    speed: SignalStatus = SignalStatus.OBSERVED
    throttle: SignalStatus = SignalStatus.OBSERVED
    brake: SignalStatus = SignalStatus.OBSERVED
    gear: SignalStatus = SignalStatus.OBSERVED
    rpm: SignalStatus = SignalStatus.OBSERVED
    steering: SignalStatus = SignalStatus.UNAVAILABLE
    brake_pressure_bar: SignalStatus = SignalStatus.UNAVAILABLE
    longitudinal_accel: SignalStatus = SignalStatus.DERIVED
    trajectory_deviation: SignalStatus = SignalStatus.DERIVED
    track_relative_lateral: SignalStatus = SignalStatus.UNAVAILABLE


class ReferenceLapProvenance(BaseModel):
    """Audit record of reference lap selection and aggregation method."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    driver_code: str
    reference_laps_used: List[int] = Field(default_factory=list)
    total_laps_analyzed: int = 0
    excluded_laps_reasons: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of lap identifier to reason for exclusion (e.g. 'Lap 1: Incident lap')"
    )
    aggregation_method: str = Field(
        default="Pointwise median across uniform 2.0m distance grid with IQR variability"
    )
    resampling_resolution_m: float = 2.0


class BaselineProfilePoint(BaseModel):
    """Uniform distance-grid sample comparing incident telemetry to nominal baseline."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    distance_m: float
    speed_baseline_kmh: float
    speed_incident_kmh: float
    speed_delta_kmh: float
    speed_iqr_kmh: float

    throttle_baseline_pct: float
    throttle_incident_pct: float
    throttle_delta_pct: float

    brake_baseline_pct: float
    brake_incident_pct: float
    brake_delta_pct: float

    x_baseline_m: Optional[float] = None
    y_baseline_m: Optional[float] = None
    x_incident_m: Optional[float] = None
    y_incident_m: Optional[float] = None
    trajectory_deviation_m: Optional[float] = None


class DriverBaselineEvidence(BaseModel):
    """Complete baseline evidence dossier for an individual involved driver."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    driver_code: str
    status: BaselineStatus
    provenance: ReferenceLapProvenance
    disruption_metrics: Optional[BaselineDisruptionMetrics] = None
    trajectory_metrics: Optional[TrajectoryDeviationMetrics] = None
    profile_sample: List[BaselineProfilePoint] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class BaselineEvidence(BaseModel):
    """Comprehensive Reference-Lap Baseline and Evidence Quantification payload."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: BaselineStatus
    drivers: Dict[str, DriverBaselineEvidence] = Field(default_factory=dict)
    summary: str
    signal_provenance: SignalProvenanceInfo = Field(default_factory=SignalProvenanceInfo)
    steward_guidance: str = Field(
        default="Reference baseline comparison quantifies physical deviation from nominal racing lines and inputs "
        "for the same car and driver. These empirical deltas inform human steward analysis and DO NOT "
        "constitute automated proof of guilt, liability, or rule infringement."
    )
