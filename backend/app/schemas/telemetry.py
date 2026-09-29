"""Pydantic schemas for synchronized telemetry timeseries."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TelemetryPointSchema(BaseModel):
    """Synchronized multi-channel telemetry frame for two interacting cars."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    time_offset: float = Field(..., description="Seconds elapsed since start of slice window")
    timestamp: str = Field(..., description="Wall-clock or elapsed time string, e.g. 13:42:18.4")

    # Driver A channels
    speed_a: float = Field(..., description="Car A speed in km/h")
    throttle_a: float = Field(..., ge=0, le=100, description="Car A throttle percentage")
    brake_a: float = Field(..., ge=0, le=100, description="Car A brake pedal/pressure percentage")
    steer_a: Optional[float] = Field(default=0.0, description="Car A steering wheel angle in degrees")
    gear_a: int = Field(default=1, ge=0, le=8, description="Car A gear")
    accel_a: float = Field(default=0.0, description="Car A acceleration in G")
    distance_a: Optional[float] = Field(default=None, description="Car A lap distance in meters")
    lap_number_a: Optional[int] = Field(default=None, description="Car A current lap number")

    # Driver B channels
    speed_b: float = Field(..., description="Car B speed in km/h")
    throttle_b: float = Field(..., ge=0, le=100, description="Car B throttle percentage")
    brake_b: float = Field(..., ge=0, le=100, description="Car B brake pedal/pressure percentage")
    steer_b: Optional[float] = Field(default=0.0, description="Car B steering wheel angle in degrees")
    gear_b: int = Field(default=1, ge=0, le=8, description="Car B gear")
    accel_b: float = Field(default=0.0, description="Car B acceleration in G")
    distance_b: Optional[float] = Field(default=None, description="Car B lap distance in meters")
    lap_number_b: Optional[int] = Field(default=None, description="Car B current lap number")

    # Derived interactive dynamics & measurements
    speed_difference: float = Field(default=0.0, description="Speed delta: speed_a - speed_b in km/h")
    gap_meters: float = Field(..., ge=0, description="Euclidean 3D proximity distance in meters")
    closing_speed_ms: float = Field(..., description="1st derivative closing velocity in m/s: -d(gap)/dt")
    lateral_dist_meters: float = Field(default=0.0, ge=0, description="Calculated lateral clearance in meters")
    same_lap: bool = Field(default=True, description="Flag indicating whether both drivers are currently on the same official lap")


class SynchronizedPairResponse(BaseModel):
    """Synchronized analysis grid response for two interacting drivers."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: str
    driver_a: str
    driver_b: str
    frequency_hz: float = Field(default=25.0, description="Temporal analysis grid frequency in Hz")
    total_points: int = Field(default=0, ge=0)
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    preprocessing_version: str = Field(default="telemetry_preprocessing_v1")
    points: List[TelemetryPointSchema] = Field(default_factory=list)


class TelemetrySliceResponse(BaseModel):
    """Bounded timeseries slice containing synchronized telemetry frames."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    incident_id: str
    session_id: str
    driver_a: str
    driver_b: str
    hz: int = Field(default=25, description="Effective sample rate in Hz")
    reference_timestamp: Optional[str] = None
    incident_window: Optional[dict] = None
    points: List[TelemetryPointSchema] = Field(default_factory=list, description="Ordered time frames")
    total_points: int = Field(default=0, ge=0)


class TelemetryQueryParams(BaseModel):
    """Constrained query parameters ensuring telemetry queries never return unconstrained rows."""

    driver_a: str = Field(..., description="Focal driver code, e.g. VER")
    driver_b: Optional[str] = Field(default=None, description="Comparison driver code, e.g. HAM")
    start_time: Optional[str] = Field(default=None, description="Start timestamp string")
    end_time: Optional[str] = Field(default=None, description="End timestamp string")
    lap: Optional[int] = Field(default=None, ge=1, description="Constrain to specific lap")
    limit: int = Field(default=500, ge=10, le=2000, description="Strict safety cap on points returned")
    resolution_hz: int = Field(default=25, ge=1, le=50, description="Downsampled target frequency")


class DriverTelemetryPointSchema(BaseModel):
    """Single channel telemetry sample point."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    timestamp: Optional[str] = None
    time_offset: float
    lap_number: Optional[int] = None
    distance: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    speed: Optional[float] = None
    throttle: Optional[float] = None
    brake: Optional[float] = None
    gear: Optional[int] = None
    rpm: Optional[int] = None
    drs: Optional[int] = None
    source: str = "fastf1"


class DriverTelemetryResponse(BaseModel):
    """Bounded telemetry stream response for a specific driver and session."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: str
    driver_code: str
    lap_number: Optional[int] = None
    total_points: int
    points: List[DriverTelemetryPointSchema]
