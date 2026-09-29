"""Feature extraction for pairwise motorsport interaction telemetry.

Computes instantaneous kinematics, acceleration profiles, vehicle response differentials,
and contextual racing behavior filters.
"""

from typing import Dict, List, Optional
import numpy as np
from pydantic import BaseModel

from app.schemas.telemetry import TelemetryPointSchema


class FrameFeatures(BaseModel):
    """Augmented kinematic and interaction features for a single synchronized frame."""
    index: int
    time_offset: float
    timestamp: str
    gap_meters: float
    closing_speed_ms: float
    speed_difference_kmh: float
    speed_a_kmh: float
    speed_b_kmh: float
    accel_a_g: float
    accel_b_g: float
    decel_delta_g: float
    throttle_a: float
    throttle_b: float
    brake_a: float
    brake_b: float
    brake_delta_pct: float
    same_lap: bool
    distance_a: Optional[float] = None
    distance_b: Optional[float] = None

    # Contextual behavioral indicators
    is_normal_slipstream: bool = False
    is_synchronized_braking: bool = False
    is_steady_following: bool = False


def extract_pairwise_features(
    frames: List[TelemetryPointSchema],
    dt_sec: float = 0.04,
) -> List[FrameFeatures]:
    """Extract multi-channel derivative and response features from synchronized frames."""
    if not frames:
        return []

    n = len(frames)
    speeds_a_mps = np.array([f.speed_a / 3.6 for f in frames])
    speeds_b_mps = np.array([f.speed_b / 3.6 for f in frames])

    # Compute longitudinal accelerations in G (dv/dt / 9.80665)
    accel_a_g = np.zeros(n, dtype=float)
    accel_b_g = np.zeros(n, dtype=float)

    if n > 1 and dt_sec > 0:
        # Central difference for interior points
        if n > 2:
            accel_a_g[1:-1] = (speeds_a_mps[2:] - speeds_a_mps[:-2]) / (2.0 * dt_sec * 9.80665)
            accel_b_g[1:-1] = (speeds_b_mps[2:] - speeds_b_mps[:-2]) / (2.0 * dt_sec * 9.80665)
        # Boundaries
        accel_a_g[0] = (speeds_a_mps[1] - speeds_a_mps[0]) / (dt_sec * 9.80665)
        accel_a_g[-1] = (speeds_a_mps[-1] - speeds_a_mps[-2]) / (dt_sec * 9.80665)
        accel_b_g[0] = (speeds_b_mps[1] - speeds_b_mps[0]) / (dt_sec * 9.80665)
        accel_b_g[-1] = (speeds_b_mps[-1] - speeds_b_mps[-2]) / (dt_sec * 9.80665)

    features_list: List[FrameFeatures] = []

    for i, f in enumerate(frames):
        a_a = round(float(accel_a_g[i]), 2)
        a_b = round(float(accel_b_g[i]), 2)
        decel_delta = round(abs(a_a - a_b), 2)
        brake_delta = round(abs(f.brake_a - f.brake_b), 2)

        # Contextual normal racing filters
        # 1. Normal slipstreaming: high throttle on both cars, closing at high speed (>220 km/h), gap > 12m
        is_slipstream = (
            f.throttle_a > 85.0
            and f.throttle_b > 85.0
            and f.speed_a > 200.0
            and f.speed_b > 200.0
            and f.gap_meters > 12.0
            and f.brake_a == 0.0
            and f.brake_b == 0.0
        )

        # 2. Synchronized corner braking: both braking heavily (brake > 40%), similar decelerations
        is_sync_braking = (
            f.brake_a > 30.0
            and f.brake_b > 30.0
            and a_a < -1.5
            and a_b < -1.5
            and decel_delta < 2.0
            and f.gap_meters > 10.0
        )

        # 3. Steady following: comfortable following distance with stable closing speed
        is_steady = (
            f.gap_meters > 20.0
            and abs(f.closing_speed_ms) < 4.0
            and decel_delta < 1.0
        )

        feat = FrameFeatures(
            index=i,
            time_offset=f.time_offset,
            timestamp=f.timestamp,
            gap_meters=f.gap_meters,
            closing_speed_ms=f.closing_speed_ms,
            speed_difference_kmh=f.speed_difference,
            speed_a_kmh=f.speed_a,
            speed_b_kmh=f.speed_b,
            accel_a_g=a_a,
            accel_b_g=a_b,
            decel_delta_g=decel_delta,
            throttle_a=f.throttle_a,
            throttle_b=f.throttle_b,
            brake_a=f.brake_a,
            brake_b=f.brake_b,
            brake_delta_pct=brake_delta,
            same_lap=f.same_lap,
            distance_a=f.distance_a,
            distance_b=f.distance_b,
            is_normal_slipstream=is_slipstream,
            is_synchronized_braking=is_sync_braking,
            is_steady_following=is_steady,
        )
        features_list.append(feat)

    return features_list
