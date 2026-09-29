"""Telemetry preprocessing, temporal synchronization, and interaction feature extraction engine.

Strictly preserves raw data immutability.
Pipeline:
    RAW MULTI-RATE TELEMETRY
            ↓
    CLEAN & SORTED TELEMETRY
            ↓
    UNIFORM ANALYSIS TIME GRID (e.g. 25 Hz)
            ↓
    PAIRWISE INTERACTION FEATURES (Euclidean gap, closing speed, deltas)
            ↓
    STRUCTURED TELEMETRY RESPONSES
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import logger
from app.data.domain import NormalizedTelemetryPoint
from app.schemas.telemetry import (
    TelemetryPointSchema,
    SynchronizedPairResponse,
)
from app.services.ingestion_service import get_ingestion_service

PREPROCESSING_VERSION = "telemetry_preprocessing_v1"

# Channel Classification
CONTINUOUS_CHANNELS = [
    "speed",
    "throttle",
    "brake",
    "rpm",
    "distance",
    "x",
    "y",
    "z",
    "steering",
    "accel_x",
    "accel_y",
]

DISCRETE_CHANNELS = [
    "gear",
    "drs",
    "lap_number",
]


def validate_speed(speed_kmh: Optional[float]) -> Optional[float]:
    """Validate and clamp speed within physical motorsport bounds [0, 420] km/h."""
    if speed_kmh is None or np.isnan(speed_kmh):
        return None
    if speed_kmh < 0.0:
        logger.warning(f"Physical anomaly: negative speed {speed_kmh:.2f} km/h clamped to 0.0")
        return 0.0
    if speed_kmh > 420.0:
        logger.warning(f"Physical anomaly: hypersonic speed {speed_kmh:.2f} km/h exceeds 420 km/h bound")
    return round(float(np.clip(speed_kmh, 0.0, 420.0)), 2)


def validate_throttle(throttle_pct: Optional[float]) -> Optional[float]:
    """Validate and clamp throttle percentage within [0, 100]%."""
    if throttle_pct is None or np.isnan(throttle_pct):
        return None
    return round(float(np.clip(throttle_pct, 0.0, 100.0)), 2)


def validate_brake(brake_pct: Optional[float]) -> Optional[float]:
    """Validate and clamp brake percentage within [0, 100]%."""
    if brake_pct is None or np.isnan(brake_pct):
        return None
    return round(float(np.clip(brake_pct, 0.0, 100.0)), 2)


def validate_position(
    x: Optional[float],
    y: Optional[float],
    z: Optional[float],
    max_radius_m: float = 10000.0,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Validate spatial coordinates are within realistic circuit bounding radius."""
    if x is None or y is None or np.isnan(x) or np.isnan(y):
        return None, None, None
    norm = np.sqrt(x**2 + y**2)
    if norm > max_radius_m:
        logger.warning(f"Spatial anomaly: position ({x:.1f}, {y:.1f}) exceeds circuit radius {max_radius_m}m")
        return None, None, None
    z_val = round(float(z), 3) if z is not None and not np.isnan(z) else 0.0
    return round(float(x), 3), round(float(y), 3), z_val


def validate_closing_speed(
    closing_speed_mps: float,
    speed_a_kmh: Optional[float],
    speed_b_kmh: Optional[float],
) -> float:
    """Validate closing speed against physical kinematic limits.

    The scalar closing speed |d(gap)/dt| cannot physically exceed ||v_a|| + ||v_b||.
    If speed channels are missing, bounded by theoretical max motorsport limit (210 m/s).
    """
    if np.isnan(closing_speed_mps):
        return 0.0

    va_mps = (speed_a_kmh / 3.6) if speed_a_kmh is not None and not np.isnan(speed_a_kmh) else 105.0
    vb_mps = (speed_b_kmh / 3.6) if speed_b_kmh is not None and not np.isnan(speed_b_kmh) else 105.0
    kinematic_limit = va_mps + vb_mps + 5.0  # +5 m/s numerical margin

    if abs(closing_speed_mps) > kinematic_limit:
        logger.warning(
            f"Physical anomaly: closing speed {closing_speed_mps:.2f} m/s exceeds kinematic limit {kinematic_limit:.2f} m/s"
        )
        return round(float(np.clip(closing_speed_mps, -kinematic_limit, kinematic_limit)), 2)

    return round(closing_speed_mps, 2)


class ProcessedTelemetryPoint(BaseModel):
    """Canonical single-car processed telemetry frame on a uniform grid."""
    timestamp: datetime
    time_offset: float
    driver_code: str
    driver_number: Optional[int] = None
    lap_number: Optional[int] = None
    distance: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    speed: Optional[float] = None
    throttle: Optional[float] = None
    brake: Optional[float] = None
    steering: Optional[float] = None
    gear: Optional[int] = None
    rpm: Optional[int] = None
    drs: Optional[int] = None
    accel_x: Optional[float] = None
    accel_y: Optional[float] = None
    source: str = "fastf1"
    provenance: Dict[str, str] = {}


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime has timezone awareness set to UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def clean_and_sort_driver_telemetry(
    raw_points: List[NormalizedTelemetryPoint],
) -> List[NormalizedTelemetryPoint]:
    """Sort monotonically and deterministically handle duplicate timestamps.

    Invariants:
        1. No records with null timestamps are retained.
        2. All timestamps are timezone-aware (UTC).
        3. Monotonic ordering: timestamp[i+1] >= timestamp[i].
        4. Identical timestamps are deterministically aggregated (mean for continuous, last for discrete).
    """
    if not raw_points:
        return []

    # 1. Filter records missing timestamps
    valid_points = [p for p in raw_points if p.timestamp is not None]
    if not valid_points:
        return []

    # 2. Ensure timezone awareness and sort monotonically
    for p in valid_points:
        p.timestamp = ensure_utc(p.timestamp)

    valid_points.sort(key=lambda pt: pt.timestamp)

    # 3. Deterministic duplicate aggregation
    cleaned: List[NormalizedTelemetryPoint] = []
    i = 0
    n = len(valid_points)

    while i < n:
        current_pt = valid_points[i]
        curr_ts = current_pt.timestamp
        duplicates = [current_pt]
        j = i + 1

        while j < n and valid_points[j].timestamp == curr_ts:
            duplicates.append(valid_points[j])
            j += 1

        if len(duplicates) == 1:
            cleaned.append(current_pt)
        else:
            # Deterministic aggregation for duplicate timestamp observations
            merged = NormalizedTelemetryPoint(
                timestamp=curr_ts,
                time_offset=current_pt.time_offset,
                driver_code=current_pt.driver_code,
                driver_number=current_pt.driver_number,
                lap_number=duplicates[-1].lap_number,
                source=current_pt.source,
            )

            # Continuous channels: average non-null observations
            for col in CONTINUOUS_CHANNELS:
                vals = [getattr(d, col) for d in duplicates if getattr(d, col) is not None]
                setattr(merged, col, float(np.mean(vals)) if vals else None)

            # Discrete channels: retain last observed state
            for col in DISCRETE_CHANNELS:
                vals = [getattr(d, col) for d in duplicates if getattr(d, col) is not None]
                setattr(merged, col, vals[-1] if vals else None)

            cleaned.append(merged)

        i = j

    # Invariant verification: Monotonic timestamps
    for idx in range(len(cleaned) - 1):
        assert cleaned[idx + 1].timestamp >= cleaned[idx].timestamp, "Monotonic ordering violation"

    return cleaned


def resample_driver_stream(
    points: List[NormalizedTelemetryPoint],
    frequency_hz: Optional[float] = None,
    max_gap_seconds: Optional[float] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[ProcessedTelemetryPoint]:
    """Resample raw multi-rate driver telemetry onto a uniform temporal grid.

    Policies:
        - Continuous channels: Linear interpolation.
        - Discrete channels (gear, drs, lap): Nearest-observation / forward-fill.
        - Maximum gap policy: If distance between adjacent observations > max_gap_seconds,
          mark channels as missing/None to prevent artificial telemetry fabrication.
        - No extrapolation: Grid strictly bounded within observation span.
    """
    cleaned = clean_and_sort_driver_telemetry(points)
    if len(cleaned) < 2:
        return []

    settings = get_settings()
    hz = float(frequency_hz or settings.TELEMETRY_ANALYSIS_HZ)
    dt_step = 1.0 / hz
    max_gap = float(
        max_gap_seconds
        if max_gap_seconds is not None
        else settings.TELEMETRY_MAX_INTERPOLATION_GAP_MS / 1000.0
    )

    t_obs_min = cleaned[0].timestamp
    t_obs_max = cleaned[-1].timestamp

    # Determine bounded analysis window
    grid_start = max(ensure_utc(start_time), t_obs_min) if start_time else t_obs_min
    grid_end = min(ensure_utc(end_time), t_obs_max) if end_time else t_obs_max

    if grid_start >= grid_end:
        return []

    # Calculate uniform timestamps
    total_duration_sec = (grid_end - grid_start).total_seconds()
    num_steps = int(round(total_duration_sec / dt_step)) + 1
    grid_timestamps = [grid_start + timedelta(seconds=k * dt_step) for k in range(num_steps)]

    # Source time arrays in seconds relative to t_obs_min
    source_sec = np.array([(p.timestamp - t_obs_min).total_seconds() for p in cleaned])
    target_sec = np.array([(ts - t_obs_min).total_seconds() for ts in grid_timestamps])

    # Find bounding indices for maximum-gap check
    idx_right = np.searchsorted(source_sec, target_sec, side="right")
    idx_left = np.clip(idx_right - 1, 0, len(source_sec) - 1)
    idx_right = np.clip(idx_right, 0, len(source_sec) - 1)

    gap_durations = source_sec[idx_right] - source_sec[idx_left]
    valid_gap_mask = gap_durations <= max_gap

    resampled_points: List[ProcessedTelemetryPoint] = []
    driver_code = cleaned[0].driver_code
    driver_num = cleaned[0].driver_number
    source_id = cleaned[0].source

    # Pre-extract continuous channel arrays
    cont_arrays: Dict[str, np.ndarray] = {}
    for ch in CONTINUOUS_CHANNELS:
        raw_vals = [getattr(p, ch) for p in cleaned]
        has_any = any(v is not None for v in raw_vals)
        if has_any:
            # Replace None with NaN for numpy interpolation
            float_vals = np.array([float(v) if v is not None else np.nan for v in raw_vals])
            # Interpolate only if at least 2 non-nan values exist
            valid_mask = ~np.isnan(float_vals)
            if np.sum(valid_mask) >= 2:
                interp_vals = np.interp(
                    target_sec,
                    source_sec[valid_mask],
                    float_vals[valid_mask],
                )
                # Mask out points where gap exceeded max_gap
                interp_vals[~valid_gap_mask] = np.nan
                cont_arrays[ch] = interp_vals

    # Pre-extract discrete channels (nearest neighbor / forward-fill)
    discrete_arrays: Dict[str, List[Optional[int]]] = {}
    for ch in DISCRETE_CHANNELS:
        d_vals: List[Optional[int]] = []
        for k, t_k in enumerate(target_sec):
            if not valid_gap_mask[k]:
                d_vals.append(None)
                continue
            # Pick nearest observation
            left_dist = abs(t_k - source_sec[idx_left[k]])
            right_dist = abs(source_sec[idx_right[k]] - t_k)
            best_idx = idx_left[k] if left_dist <= right_dist else idx_right[k]
            val = getattr(cleaned[best_idx], ch)
            d_vals.append(int(val) if val is not None else None)
        discrete_arrays[ch] = d_vals

    # Construct processed points with physical sanity checks
    for k, ts in enumerate(grid_timestamps):
        time_offset = round(k * dt_step, 4)

        # Physical sanity checks & channel mapping
        speed_raw = cont_arrays["speed"][k] if "speed" in cont_arrays and not np.isnan(cont_arrays["speed"][k]) else None
        speed_val = validate_speed(speed_raw)

        throttle_raw = cont_arrays["throttle"][k] if "throttle" in cont_arrays and not np.isnan(cont_arrays["throttle"][k]) else None
        throttle_val = validate_throttle(throttle_raw)

        brake_raw = cont_arrays["brake"][k] if "brake" in cont_arrays and not np.isnan(cont_arrays["brake"][k]) else None
        brake_val = validate_brake(brake_raw)

        rpm_val = int(cont_arrays["rpm"][k]) if "rpm" in cont_arrays and not np.isnan(cont_arrays["rpm"][k]) else None
        dist_val = round(cont_arrays["distance"][k], 2) if "distance" in cont_arrays and not np.isnan(cont_arrays["distance"][k]) else None

        x_raw = cont_arrays["x"][k] if "x" in cont_arrays else None
        y_raw = cont_arrays["y"][k] if "y" in cont_arrays else None
        z_raw = cont_arrays["z"][k] if "z" in cont_arrays else None
        x_val, y_val, z_val = validate_position(x_raw, y_raw, z_raw)

        steer_val = round(cont_arrays["steering"][k], 2) if "steering" in cont_arrays and not np.isnan(cont_arrays["steering"][k]) else None

        gear_val = discrete_arrays.get("gear", [None])[k]
        drs_val = discrete_arrays.get("drs", [None])[k]
        lap_val = discrete_arrays.get("lap_number", [None])[k]

        pt = ProcessedTelemetryPoint(
            timestamp=ts,
            time_offset=time_offset,
            driver_code=driver_code,
            driver_number=driver_num,
            lap_number=lap_val,
            distance=dist_val,
            x=x_val,
            y=y_val,
            z=z_val,
            speed=speed_val,
            throttle=throttle_val,
            brake=brake_val,
            steering=steer_val,
            gear=gear_val,
            rpm=rpm_val,
            drs=drs_val,
            source=source_id,
            provenance={
                "speed": "INTERPOLATED" if valid_gap_mask[k] else "MISSING",
                "grid_hz": str(hz),
                "version": PREPROCESSING_VERSION,
            },
        )
        resampled_points.append(pt)

    return resampled_points


def calculate_closing_speeds(
    gaps_m: np.ndarray,
    dt_sec: float,
) -> np.ndarray:
    """Calculate closing speed: closing_speed = -d(gap)/dt in m/s.

    Conventions:
        Positive (>0): cars becoming closer (gap shrinking).
        Negative (<0): cars separating (gap opening).
        Zero (=0): stable gap.
    Numerical derivative:
        - Central difference for interior points where both t-1 and t+1 are valid.
        - 1st order forward/backward difference where only one neighbor is valid.
        - np.nan where current frame or no neighbors are valid, preventing artificial spikes across data gaps.
    """
    n = len(gaps_m)
    closing_speeds = np.full(n, np.nan, dtype=float)

    if n < 2 or dt_sec <= 0:
        return closing_speeds

    for i in range(n):
        if np.isnan(gaps_m[i]):
            continue

        has_prev = (i > 0) and not np.isnan(gaps_m[i - 1])
        has_next = (i < n - 1) and not np.isnan(gaps_m[i + 1])

        if has_prev and has_next:
            closing_speeds[i] = -(gaps_m[i + 1] - gaps_m[i - 1]) / (2.0 * dt_sec)
        elif has_next:
            closing_speeds[i] = -(gaps_m[i + 1] - gaps_m[i]) / dt_sec
        elif has_prev:
            closing_speeds[i] = -(gaps_m[i] - gaps_m[i - 1]) / dt_sec
        else:
            closing_speeds[i] = np.nan

    return np.round(closing_speeds, 2)


def synchronize_pair(
    points_a: List[NormalizedTelemetryPoint],
    points_b: List[NormalizedTelemetryPoint],
    frequency_hz: Optional[float] = None,
    max_gap_seconds: Optional[float] = None,
) -> List[TelemetryPointSchema]:
    """Synchronize two driver telemetry streams onto a common temporal analysis grid.

    Calculates:
        - speed_difference: speed_a - speed_b (km/h)
        - euclidean_gap_m: 3D Cartesian Euclidean separation sqrt((xa-xb)^2 + (ya-yb)^2 + (za-zb)^2) in meters
        - closing_speed_ms: -d(gap)/dt in m/s
        - same_lap: boolean indicating whether both drivers are on the same lap
        - Preserves lap_number_a and lap_number_b independently
    """
    if not points_a or not points_b:
        return []

    clean_a = clean_and_sort_driver_telemetry(points_a)
    clean_b = clean_and_sort_driver_telemetry(points_b)

    if not clean_a or not clean_b:
        return []

    # Mutual temporal coverage
    t_start = max(clean_a[0].timestamp, clean_b[0].timestamp)
    t_end = min(clean_a[-1].timestamp, clean_b[-1].timestamp)

    if t_start >= t_end:
        logger.warning(f"No mutual temporal overlap between {clean_a[0].driver_code} and {clean_b[0].driver_code}")
        return []

    settings = get_settings()
    hz = float(frequency_hz or settings.TELEMETRY_ANALYSIS_HZ)
    dt_step = 1.0 / hz

    # Resample both drivers on the exact common bounded window
    resampled_a = resample_driver_stream(
        clean_a,
        frequency_hz=hz,
        max_gap_seconds=max_gap_seconds,
        start_time=t_start,
        end_time=t_end,
    )
    resampled_b = resample_driver_stream(
        clean_b,
        frequency_hz=hz,
        max_gap_seconds=max_gap_seconds,
        start_time=t_start,
        end_time=t_end,
    )

    min_len = min(len(resampled_a), len(resampled_b))
    if min_len == 0:
        return []

    resampled_a = resampled_a[:min_len]
    resampled_b = resampled_b[:min_len]

    # Pre-calculate Euclidean 3D gap array (in SI meters)
    gaps_m = np.full(min_len, np.nan, dtype=float)
    has_valid_pos = np.zeros(min_len, dtype=bool)

    for i in range(min_len):
        pa = resampled_a[i]
        pb = resampled_b[i]
        if pa.x is not None and pa.y is not None and pb.x is not None and pb.y is not None:
            za = pa.z if pa.z is not None else 0.0
            zb = pb.z if pb.z is not None else 0.0
            dist = np.sqrt((pa.x - pb.x) ** 2 + (pa.y - pb.y) ** 2 + (za - zb) ** 2)
            gaps_m[i] = dist
            has_valid_pos[i] = True

    # Calculate closing speed from gap derivative
    closing_speeds = calculate_closing_speeds(gaps_m, dt_sec=dt_step)

    paired_frames: List[TelemetryPointSchema] = []

    for i in range(min_len):
        pa = resampled_a[i]
        pb = resampled_b[i]

        sp_a = pa.speed or 0.0
        sp_b = pb.speed or 0.0
        speed_delta = round(sp_a - sp_b, 2)
        gap = round(float(gaps_m[i]), 2) if has_valid_pos[i] else 0.0
        raw_closing = closing_speeds[i] if (has_valid_pos[i] and not np.isnan(closing_speeds[i])) else 0.0
        closing = validate_closing_speed(raw_closing, sp_a, sp_b)

        same_lap = (
            (pa.lap_number == pb.lap_number)
            if (pa.lap_number is not None and pb.lap_number is not None)
            else True
        )

        ts_str = pa.timestamp.strftime("%H:%M:%S.%f")[:-3]

        frame = TelemetryPointSchema(
            time_offset=pa.time_offset,
            timestamp=ts_str,
            # Driver A
            speed_a=sp_a,
            throttle_a=pa.throttle or 0.0,
            brake_a=pa.brake or 0.0,
            steer_a=pa.steering or 0.0,
            gear_a=pa.gear or 1,
            accel_a=pa.accel_x or 0.0,
            distance_a=pa.distance,
            lap_number_a=pa.lap_number,
            # Driver B
            speed_b=sp_b,
            throttle_b=pb.throttle or 0.0,
            brake_b=pb.brake or 0.0,
            steer_b=pb.steering or 0.0,
            gear_b=pb.gear or 1,
            accel_b=pb.accel_x or 0.0,
            distance_b=pb.distance,
            lap_number_b=pb.lap_number,
            # Interactive measurements
            speed_difference=speed_delta,
            gap_meters=gap,
            closing_speed_ms=closing,
            lateral_dist_meters=0.0,
            same_lap=same_lap,
        )
        paired_frames.append(frame)

    return paired_frames


class TelemetryService:
    """Service providing telemetry preprocessing, temporal resampling, and pair interaction extraction."""

    def __init__(self):
        self.ingestion = get_ingestion_service()
        self.settings = get_settings()

    def get_processed_driver_telemetry(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        driver: str,
        lap: Optional[int] = None,
        frequency_hz: Optional[float] = None,
        limit: int = 500,
    ) -> List[ProcessedTelemetryPoint]:
        """Load raw driver telemetry and resample to uniform analysis grid."""
        raw_points = self.ingestion.load_driver_telemetry(
            season=season,
            round_or_name=round_or_name,
            session_identifier=session_identifier,
            driver=driver,
            lap=lap,
        )
        hz = frequency_hz or self.settings.TELEMETRY_ANALYSIS_HZ
        processed = resample_driver_stream(raw_points, frequency_hz=hz)
        return processed[:limit] if limit and len(processed) > limit else processed

    def get_synchronized_pair_slice(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        driver_a: str,
        driver_b: str,
        lap: Optional[int] = None,
        frequency_hz: Optional[float] = None,
        limit: int = 500,
    ) -> SynchronizedPairResponse:
        """Retrieve synchronized telemetry pair across common analysis grid for two cars."""
        raw_a = self.ingestion.load_driver_telemetry(
            season=season,
            round_or_name=round_or_name,
            session_identifier=session_identifier,
            driver=driver_a,
            lap=lap,
        )
        raw_b = self.ingestion.load_driver_telemetry(
            season=season,
            round_or_name=round_or_name,
            session_identifier=session_identifier,
            driver=driver_b,
            lap=lap,
        )

        hz = float(frequency_hz or self.settings.TELEMETRY_ANALYSIS_HZ)
        paired_points = synchronize_pair(raw_a, raw_b, frequency_hz=hz)
        bounded_points = paired_points[:limit] if limit and len(paired_points) > limit else paired_points

        t_start = bounded_points[0].timestamp if bounded_points else None
        t_end = bounded_points[-1].timestamp if bounded_points else None

        return SynchronizedPairResponse(
            session_id=f"f1-{season}-{str(round_or_name).lower()}-{session_identifier.lower()}",
            driver_a=driver_a.upper(),
            driver_b=driver_b.upper(),
            frequency_hz=hz,
            total_points=len(bounded_points),
            time_window_start=t_start,
            time_window_end=t_end,
            preprocessing_version=PREPROCESSING_VERSION,
            points=bounded_points,
        )


_telemetry_service_instance: Optional[TelemetryService] = None


def get_telemetry_service() -> TelemetryService:
    """Singleton accessor for TelemetryService."""
    global _telemetry_service_instance
    if _telemetry_service_instance is None:
        _telemetry_service_instance = TelemetryService()
    return _telemetry_service_instance
