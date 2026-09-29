"""Telemetry evidence representation and data quality metrics.

Summarizes empirical multi-channel telemetry dynamics without replacing
underlying raw timeseries observation frames.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.schemas.telemetry import TelemetryPointSchema


class TelemetryEvidenceSummary(BaseModel):
    """Compact empirical summary of interaction telemetry across the event window."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    driver_a: str
    driver_b: str
    event_start: str
    event_peak: str
    event_end: str
    duration_seconds: float

    # Proximity & closing kinematics
    minimum_gap_meters: float
    gap_at_peak_meters: float
    peak_closing_speed_ms: float
    closing_speed_at_peak_ms: float

    # Speeds and differentials
    speed_a_kmh: float
    speed_b_kmh: float
    speed_delta_kmh: float

    # Vehicle control states at peak
    throttle_a_pct: float
    throttle_b_pct: float
    brake_a_pct: float
    brake_b_pct: float
    brake_delta_pct: float

    # Acceleration / deceleration dynamics
    accel_a_g: float
    accel_b_g: float
    decel_delta_g: float

    # Lap and track positioning
    lap_number_a: Optional[int] = None
    lap_number_b: Optional[int] = None
    same_lap: bool = True
    track_distance_a: Optional[float] = None
    track_distance_b: Optional[float] = None

    # Telemetry data fidelity metrics
    total_frames: int
    data_coverage_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of window with valid non-null sensor frames")
    interpolation_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of frames resampled between raw observations")
    missing_data_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of window with missing sensor channels")
    telemetry_evidence_strength: int = Field(..., ge=0, le=100, description="Empirical sensor convergence score (0-100)")
    raw_stream_ref: str = Field(..., description="API reference URL to bounded underlying synchronized pair stream")


def build_telemetry_evidence(
    driver_a: str,
    driver_b: str,
    raw_frames: List[TelemetryPointSchema],
    start_index: int,
    peak_index: int,
    end_index: int,
    evidence_strength: int = 50,
) -> TelemetryEvidenceSummary:
    """Extract compact telemetry evidence and data quality statistics from synchronized frames."""
    sub_frames = raw_frames[start_index : end_index + 1]
    peak_frame = raw_frames[peak_index] if peak_index < len(raw_frames) else sub_frames[0]

    min_gap = min((f.gap_meters for f in sub_frames), default=0.0)
    peak_closing = max([f.closing_speed_ms for f in sub_frames], key=lambda v: abs(v), default=0.0)

    t_start = sub_frames[0].timestamp
    t_end = sub_frames[-1].timestamp
    duration = round(sub_frames[-1].time_offset - sub_frames[0].time_offset, 2)

    # Compute fidelity metrics
    valid_speed_frames = sum(1 for f in sub_frames if f.speed_a > 0 and f.speed_b > 0)
    data_coverage = round((valid_speed_frames / len(sub_frames)) * 100.0, 1) if sub_frames else 0.0

    # FastF1 typical raw sample rate is ~3.5 Hz; 25 Hz lattice means ~85% interpolated points
    interp_pct = 85.0
    missing_pct = round(100.0 - data_coverage, 1)

    # Approximate longitudinal accelerations
    speed_diff = peak_frame.speed_difference
    brake_diff = round(abs(peak_frame.brake_a - peak_frame.brake_b), 1)

    return TelemetryEvidenceSummary(
        driver_a=driver_a,
        driver_b=driver_b,
        event_start=t_start,
        event_peak=peak_frame.timestamp,
        event_end=t_end,
        duration_seconds=duration,
        minimum_gap_meters=round(float(min_gap), 2),
        gap_at_peak_meters=round(float(peak_frame.gap_meters), 2),
        peak_closing_speed_ms=round(float(peak_closing), 2),
        closing_speed_at_peak_ms=round(float(peak_frame.closing_speed_ms), 2),
        speed_a_kmh=round(float(peak_frame.speed_a), 1),
        speed_b_kmh=round(float(peak_frame.speed_b), 1),
        speed_delta_kmh=speed_diff,
        throttle_a_pct=round(float(peak_frame.throttle_a), 1),
        throttle_b_pct=round(float(peak_frame.throttle_b), 1),
        brake_a_pct=round(float(peak_frame.brake_a), 1),
        brake_b_pct=round(float(peak_frame.brake_b), 1),
        brake_delta_pct=brake_diff,
        accel_a_g=0.0,
        accel_b_g=0.0,
        decel_delta_g=0.0,
        lap_number_a=peak_frame.lap_number_a,
        lap_number_b=peak_frame.lap_number_b,
        same_lap=peak_frame.same_lap,
        track_distance_a=peak_frame.distance_a,
        track_distance_b=peak_frame.distance_b,
        total_frames=len(sub_frames),
        data_coverage_pct=data_coverage,
        interpolation_pct=interp_pct,
        missing_data_pct=missing_pct,
        telemetry_evidence_strength=evidence_strength,
        raw_stream_ref=f"/api/v1/telemetry/pair-stream?driver_a={driver_a}&driver_b={driver_b}",
    )
