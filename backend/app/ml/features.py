"""Feature engineering and tabular vectorization for ML candidate evaluation.

CRITICAL GUARDRAILS & MISSING-VALUE INTEGRITY (PROMPT 11):
    1. EXCLUDES driver identities, team names, session IDs, turn names, and timestamps.
    2. Strictly extracts kinematic, baseline deviation, geometric, and data quality indicators.
    3. Explicit Missingness Flags: Missing sensors (brake, throttle, baseline, geometry, exit clearance)
       MUST NOT be silently converted into physically meaningful zeros without an explicit indicator.
    4. Guarantees deterministic float vector outputs with documented, feature-specific imputation.
"""

from typing import Any, Dict, List, Optional
import numpy as np

# Canonical feature schema for Prompt 10 backwards-compatibility
FEATURE_NAMES_V1 = [
    "min_gap_m",
    "peak_closing_speed_ms",
    "mean_closing_speed_ms",
    "speed_delta_kmh",
    "brake_delta_pct",
    "throttle_delta_pct",
    "accel_delta_g",
    "max_trajectory_dev_m",
    "mean_trajectory_dev_m",
    "braking_onset_delta_m",
    "apex_speed_dev_kmh",
    "apex_delta_s_m",
    "apex_overlap_pct",
    "front_axle_gap_m",
    "exit_clearance_m",
    "relative_position_code",
    "sync_flag",
    "missing_telemetry_flag",
    "sample_density",
]

# Hardened Prompt 11 canonical feature schema with explicit missing-value indicators
FEATURE_NAMES_V1_1 = [
    # Kinematics
    "min_gap_m",
    "peak_closing_speed_ms",
    "mean_closing_speed_ms",
    "speed_delta_kmh",
    "brake_delta_pct",
    "throttle_delta_pct",
    "accel_delta_g",
    # Reference-Lap Baseline Deviations
    "max_trajectory_dev_m",
    "mean_trajectory_dev_m",
    "braking_onset_delta_m",
    "apex_speed_dev_kmh",
    # Cornering Overtake Geometry
    "apex_delta_s_m",
    "apex_overlap_pct",
    "front_axle_gap_m",
    "exit_clearance_m",
    "relative_position_code",
    # Data Quality & Explicit Missing-Sensor Indicators (Audit Compliance)
    "sync_flag",
    "missing_telemetry_flag",
    "missing_brake_flag",
    "missing_throttle_flag",
    "missing_baseline_flag",
    "missing_geometry_flag",
    "missing_exit_clearance_flag",
    "sample_density",
]

# Active canonical feature schema
FEATURE_NAMES = FEATURE_NAMES_V1_1
FEATURE_VERSION = "v1.1"

# Documented default imputation values for unobserved channels
# Accompanied by explicit missing_*_flag indicators to prevent silent zero misinterpretation
DEFAULT_FEATURE_VALUES: Dict[str, float] = {
    "min_gap_m": 15.0,                 # Non-interacting vehicle spacing sentinel (>12m proximity threshold)
    "peak_closing_speed_ms": 0.0,      # Zero closure sentinel
    "mean_closing_speed_ms": 0.0,
    "speed_delta_kmh": 0.0,
    "brake_delta_pct": 0.0,            # Sentinel paired with missing_brake_flag=1.0
    "throttle_delta_pct": 0.0,         # Sentinel paired with missing_throttle_flag=1.0
    "accel_delta_g": 0.0,
    "max_trajectory_dev_m": 0.0,       # Sentinel paired with missing_baseline_flag=1.0
    "mean_trajectory_dev_m": 0.0,
    "braking_onset_delta_m": 0.0,
    "apex_speed_dev_kmh": 0.0,
    "apex_delta_s_m": 10.0,            # Non-overlapped longitudinal gap sentinel
    "apex_overlap_pct": 0.0,
    "front_axle_gap_m": 10.0,
    "exit_clearance_m": 2.0,           # Baseline one-car-width regulation reference sentinel
    "relative_position_code": 0.0,     # Alongside / neutral
    "sync_flag": 1.0,
    "missing_telemetry_flag": 0.0,
    "missing_brake_flag": 0.0,
    "missing_throttle_flag": 0.0,
    "missing_baseline_flag": 0.0,
    "missing_geometry_flag": 0.0,
    "missing_exit_clearance_flag": 0.0,
    "sample_density": 25.0,
}


def extract_features_from_dict(
    raw_dict: Dict[str, Any],
    feature_schema: Optional[List[str]] = None,
) -> Dict[str, float]:
    """Deterministically map a dictionary of raw measurements to the canonical feature schema.
    
    Preserves unobserved sensor flags rather than silently imputing misleading zero observations.
    """
    schema = feature_schema or FEATURE_NAMES
    features: Dict[str, float] = {}

    for name in schema:
        val = raw_dict.get(name)
        if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
            # If the feature itself is a missingness flag, default to 1.0 (unobserved) if parent channel was absent
            if name.startswith("missing_") and name not in raw_dict:
                # Infer missing flag from corresponding primary signal
                signal_map = {
                    "missing_brake_flag": "brake_delta_pct",
                    "missing_throttle_flag": "throttle_delta_pct",
                    "missing_baseline_flag": "max_trajectory_dev_m",
                    "missing_geometry_flag": "apex_delta_s_m",
                    "missing_exit_clearance_flag": "exit_clearance_m",
                }
                parent = signal_map.get(name)
                if parent and parent not in raw_dict:
                    features[name] = 1.0
                else:
                    features[name] = DEFAULT_FEATURE_VALUES.get(name, 0.0)
            else:
                features[name] = DEFAULT_FEATURE_VALUES.get(name, 0.0)
        else:
            try:
                features[name] = float(val)
            except (ValueError, TypeError):
                features[name] = DEFAULT_FEATURE_VALUES.get(name, 0.0)

    return features


def extract_features_from_dossier_data(
    candidate: Any,
    telemetry_frames: Optional[List[Any]] = None,
    baseline_evidence: Optional[Any] = None,
    overtake_geometry: Optional[Any] = None,
    feature_schema: Optional[List[str]] = None,
) -> Dict[str, float]:
    """Extract canonical feature dictionary from candidate dossier and multi-modal evidence objects."""
    schema = feature_schema or FEATURE_NAMES
    raw: Dict[str, Any] = {}

    # 1. Telemetry frames kinematics
    if telemetry_frames and len(telemetry_frames) > 0:
        gaps = [
            float(f.gap_meters)
            for f in telemetry_frames
            if getattr(f, "gap_meters", None) is not None and f.gap_meters > 0
        ]
        closing_speeds = [
            float(f.closing_speed_ms)
            for f in telemetry_frames
            if getattr(f, "closing_speed_ms", None) is not None
        ]

        raw["min_gap_m"] = min(gaps) if gaps else DEFAULT_FEATURE_VALUES["min_gap_m"]
        raw["peak_closing_speed_ms"] = max(closing_speeds) if closing_speeds else 0.0
        raw["mean_closing_speed_ms"] = float(np.mean(closing_speeds)) if closing_speeds else 0.0

        # Closest proximity frame
        closest_idx = int(np.argmin(gaps)) if gaps else len(telemetry_frames) // 2
        cf = telemetry_frames[min(closest_idx, len(telemetry_frames) - 1)]
        raw["speed_delta_kmh"] = abs(float(getattr(cf, "speed_a", 0.0) - getattr(cf, "speed_b", 0.0)))

        # Brake channel verification
        ba = getattr(cf, "brake_a", None)
        bb = getattr(cf, "brake_b", None)
        if ba is not None and bb is not None:
            raw["brake_delta_pct"] = abs(float(ba - bb))
            raw["missing_brake_flag"] = 0.0
        else:
            raw["brake_delta_pct"] = DEFAULT_FEATURE_VALUES["brake_delta_pct"]
            raw["missing_brake_flag"] = 1.0

        # Throttle channel verification
        ta = getattr(cf, "throttle_a", None)
        tb = getattr(cf, "throttle_b", None)
        if ta is not None and tb is not None:
            raw["throttle_delta_pct"] = abs(float(ta - tb))
            raw["missing_throttle_flag"] = 0.0
        else:
            raw["throttle_delta_pct"] = DEFAULT_FEATURE_VALUES["throttle_delta_pct"]
            raw["missing_throttle_flag"] = 1.0

        raw["accel_delta_g"] = abs(float(getattr(cf, "accel_a", 0.0) - getattr(cf, "accel_b", 0.0)))
        raw["sync_flag"] = 1.0
        raw["missing_telemetry_flag"] = 0.0
        raw["sample_density"] = float(len(telemetry_frames))
    else:
        raw["min_gap_m"] = DEFAULT_FEATURE_VALUES["min_gap_m"]
        raw["missing_telemetry_flag"] = 1.0
        raw["missing_brake_flag"] = 1.0
        raw["missing_throttle_flag"] = 1.0
        raw["sample_density"] = 0.0

    # 2. Reference-Lap Baseline Deviation
    if baseline_evidence and getattr(baseline_evidence, "status", None) != "INSUFFICIENT_REFERENCE_DATA":
        raw["max_trajectory_dev_m"] = getattr(baseline_evidence, "max_trajectory_deviation_m", 0.0) or 0.0
        raw["mean_trajectory_dev_m"] = getattr(baseline_evidence, "mean_trajectory_deviation_m", 0.0) or 0.0
        raw["braking_onset_delta_m"] = getattr(baseline_evidence, "braking_onset_delta_m", 0.0) or 0.0
        raw["apex_speed_dev_kmh"] = getattr(baseline_evidence, "apex_speed_delta_kmh", 0.0) or 0.0
        raw["missing_baseline_flag"] = 0.0
    else:
        raw["max_trajectory_dev_m"] = DEFAULT_FEATURE_VALUES["max_trajectory_dev_m"]
        raw["mean_trajectory_dev_m"] = DEFAULT_FEATURE_VALUES["mean_trajectory_dev_m"]
        raw["braking_onset_delta_m"] = DEFAULT_FEATURE_VALUES["braking_onset_delta_m"]
        raw["apex_speed_dev_kmh"] = DEFAULT_FEATURE_VALUES["apex_speed_dev_kmh"]
        raw["missing_baseline_flag"] = 1.0

    # 3. Cornering Overtake Geometry
    if overtake_geometry and getattr(overtake_geometry, "apex_snapshot", None):
        apex_snap = overtake_geometry.apex_snapshot
        raw["apex_delta_s_m"] = abs(getattr(apex_snap, "longitudinal_gap_m", 10.0) or 10.0)
        raw["apex_overlap_pct"] = getattr(apex_snap, "overlap_percent", 0.0) or 0.0
        raw["front_axle_gap_m"] = getattr(apex_snap, "front_axle_gap_m", 10.0) or 10.0
        rel_pos = getattr(apex_snap, "relative_position", None)
        rel_str = str(rel_pos.value if hasattr(rel_pos, "value") else rel_pos).upper()
        if "AHEAD" in rel_str:
            raw["relative_position_code"] = 1.0
        elif "BEHIND" in rel_str:
            raw["relative_position_code"] = -1.0
        else:
            raw["relative_position_code"] = 0.0
        raw["missing_geometry_flag"] = 0.0

        exit_clear = getattr(overtake_geometry, "exit_clearance", None)
        if exit_clear and getattr(exit_clear, "measured_clearance_m", None) is not None:
            raw["exit_clearance_m"] = float(exit_clear.measured_clearance_m)
            raw["missing_exit_clearance_flag"] = 0.0
        else:
            raw["exit_clearance_m"] = DEFAULT_FEATURE_VALUES["exit_clearance_m"]
            raw["missing_exit_clearance_flag"] = 1.0
    else:
        raw["apex_delta_s_m"] = DEFAULT_FEATURE_VALUES["apex_delta_s_m"]
        raw["apex_overlap_pct"] = DEFAULT_FEATURE_VALUES["apex_overlap_pct"]
        raw["front_axle_gap_m"] = DEFAULT_FEATURE_VALUES["front_axle_gap_m"]
        raw["exit_clearance_m"] = DEFAULT_FEATURE_VALUES["exit_clearance_m"]
        raw["relative_position_code"] = 0.0
        raw["missing_geometry_flag"] = 1.0
        raw["missing_exit_clearance_flag"] = 1.0

    return extract_features_from_dict(raw, feature_schema=schema)


def vectorize_features(
    features: Dict[str, float],
    feature_schema: Optional[List[str]] = None,
) -> np.ndarray:
    """Convert feature dictionary to 1D numpy array ordered by the chosen feature schema."""
    schema = feature_schema or FEATURE_NAMES
    return np.array([features.get(name, DEFAULT_FEATURE_VALUES.get(name, 0.0)) for name in schema], dtype=np.float64)
