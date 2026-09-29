"""Real-data validation script for telemetry preprocessing and pair synchronization.

Validates 3 driver pairs on the 2024 Italian Grand Prix (Monza) Race:
1. Charles Leclerc (LEC) vs Kevin Magnussen (MAG)
2. Charles Leclerc (LEC) vs Carlos Sainz (SAI)
3. Kevin Magnussen (MAG) vs Pierre Gasly (GAS)
"""

import sys
import time
from pathlib import Path
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import logger
from app.services.ingestion_service import get_ingestion_service
from app.services.telemetry_service import (
    clean_and_sort_driver_telemetry,
    resample_driver_stream,
    synchronize_pair,
    PREPROCESSING_VERSION,
)


def validate_driver_stream(driver_code: str, raw_points, target_hz: float = 25.0):
    """Numerically validate single driver stream resampling."""
    dt_target = 1.0 / target_hz

    # 1. Clean & Sort
    cleaned = clean_and_sort_driver_telemetry(raw_points)
    assert len(cleaned) > 0, f"No cleaned points for {driver_code}"

    # Monotonicity check
    for i in range(len(cleaned) - 1):
        assert cleaned[i + 1].timestamp >= cleaned[i].timestamp, "Cleaned stream not monotonic"

    # 2. Resample to 25 Hz grid
    t0 = time.time()
    resampled = resample_driver_stream(cleaned, frequency_hz=target_hz)
    resample_time = time.time() - t0

    assert len(resampled) > 0, f"Resampling produced 0 points for {driver_code}"

    # Timestep spacing verification
    timesteps = [
        (resampled[i + 1].timestamp - resampled[i].timestamp).total_seconds()
        for i in range(len(resampled) - 1)
    ]
    median_dt = float(np.median(timesteps))
    mean_dt = float(np.mean(timesteps))
    max_dt_error = float(np.max(np.abs(np.array(timesteps) - dt_target)))

    # Invariant assertions
    assert np.isclose(median_dt, dt_target, atol=1e-4), f"Median timestep {median_dt} != {dt_target}"
    assert max_dt_error < 1e-3, f"Max timestep error {max_dt_error} exceeds 1ms tolerance"

    # Physical sanity checks on resampled values
    valid_speeds = [p.speed for p in resampled if p.speed is not None]
    valid_throttles = [p.throttle for p in resampled if p.throttle is not None]
    valid_brakes = [p.brake for p in resampled if p.brake is not None]
    valid_gears = [p.gear for p in resampled if p.gear is not None]

    assert all(s >= 0 for s in valid_speeds), "Negative speed detected"
    assert all(0 <= th <= 100 for th in valid_throttles), "Throttle outside [0, 100]"
    assert all(0 <= br <= 100 for br in valid_brakes), "Brake outside [0, 100]"
    assert all(isinstance(g, int) and 0 <= g <= 8 for g in valid_gears), "Gear not discrete integer [0, 8]"

    return {
        "driver": driver_code,
        "raw_points": len(raw_points),
        "cleaned_points": len(cleaned),
        "resampled_points": len(resampled),
        "median_dt": median_dt,
        "mean_dt": mean_dt,
        "max_dt_error": max_dt_error,
        "resample_time_sec": resample_time,
        "speed_range": (min(valid_speeds), max(valid_speeds)) if valid_speeds else (0, 0),
    }


def validate_pair(
    pair_name: str,
    driver_a: str,
    driver_b: str,
    raw_a,
    raw_b,
    target_hz: float = 25.0,
):
    """Validate pairwise synchronization, Euclidean gap, and closing speed."""
    t0 = time.time()
    synced_frames = synchronize_pair(raw_a, raw_b, frequency_hz=target_hz)
    sync_time = time.time() - t0

    assert len(synced_frames) > 0, f"No synchronized frames for pair {pair_name}"

    gaps = [f.gap_meters for f in synced_frames]
    closing_speeds = [f.closing_speed_ms for f in synced_frames]
    speed_deltas = [f.speed_difference for f in synced_frames]

    # Verify no negative gaps
    assert all(g >= 0 for g in gaps), "Negative Euclidean gap detected"

    # Verify independent lap preservation
    laps_a = {f.lap_number_a for f in synced_frames if f.lap_number_a is not None}
    laps_b = {f.lap_number_b for f in synced_frames if f.lap_number_b is not None}

    print(f"\n--- PAIR VALIDATION: {pair_name} ({driver_a} vs {driver_b}) ---")
    print(f"Synchronized Frames: {len(synced_frames)} frames @ {target_hz} Hz ({len(synced_frames) * (1.0/target_hz):.1f}s window)")
    print(f"Sync Processing Time: {sync_time:.4f}s")
    print(f"Euclidean Gap Range: Min={min(gaps):.2f}m, Max={max(gaps):.2f}m, Median={float(np.median(gaps)):.2f}m")
    print(f"Closing Speed Range: Min={min(closing_speeds):.2f} m/s, Max={max(closing_speeds):.2f} m/s, Mean={float(np.mean(closing_speeds)):.2f} m/s")
    print(f"Speed Delta (A - B): Min={min(speed_deltas):.2f} km/h, Max={max(speed_deltas):.2f} km/h, Median={float(np.median(speed_deltas)):.2f} km/h")
    print(f"Driver A Laps Observed: {sorted(list(laps_a))}")
    print(f"Driver B Laps Observed: {sorted(list(laps_b))}")

    # Inspect a sample frame
    sample = synced_frames[len(synced_frames) // 2]
    print(f"Sample Frame at Offset {sample.time_offset:.2f}s ({sample.timestamp}):")
    print(f"  {driver_a}: Speed={sample.speed_a} km/h, Throttle={sample.throttle_a}%, Brake={sample.brake_a}%, Gear={sample.gear_a}, Lap={sample.lap_number_a}")
    print(f"  {driver_b}: Speed={sample.speed_b} km/h, Throttle={sample.throttle_b}%, Brake={sample.brake_b}%, Gear={sample.gear_b}, Lap={sample.lap_number_b}")
    print(f"  Interaction: SpeedDelta={sample.speed_difference} km/h, Gap={sample.gap_meters}m, ClosingSpeed={sample.closing_speed_ms} m/s")

    return {
        "pair": pair_name,
        "frames": len(synced_frames),
        "sync_time": sync_time,
        "gap_min": min(gaps),
        "gap_max": max(gaps),
        "closing_min": min(closing_speeds),
        "closing_max": max(closing_speeds),
    }


def run_monza_real_validation():
    """Execute complete validation suite across 3 pairs on 2024 Monza Race."""
    print("=" * 70)
    print("PROMPT 04: REAL DATA PREPROCESSING & SYNCHRONIZATION VALIDATION")
    print("Session: 2024 Italian Grand Prix (Monza) - Race")
    print("=" * 70)

    ingestion = get_ingestion_service()

    # Load bounded telemetry for Lap 10 of LEC, MAG, SAI, GAS
    drivers_to_load = ["LEC", "MAG", "SAI", "GAS"]
    raw_data = {}

    print(f"\n[1/3] Loading Lap 10 raw telemetry for drivers: {drivers_to_load}...")
    for drv in drivers_to_load:
        t0 = time.time()
        pts = ingestion.load_driver_telemetry(
            season=2024,
            round_or_name="Monza",
            session_identifier="Race",
            driver=drv,
            lap=10,
        )
        print(f"  Loaded {drv}: {len(pts)} raw observations in {time.time() - t0:.2f}s")
        assert len(pts) > 0, f"No raw observations returned for {drv}"
        raw_data[drv] = pts

    print("\n[2/3] Validating single-driver resampling & numerical bounds (25 Hz)...")
    stream_stats = []
    for drv, pts in raw_data.items():
        stat = validate_driver_stream(drv, pts, target_hz=25.0)
        stream_stats.append(stat)
        print(f"  {drv}: Raw={stat['raw_points']} -> Resampled={stat['resampled_points']} @ 25Hz, Median dt={stat['median_dt']:.4f}s, Speed: {stat['speed_range'][0]}-{stat['speed_range'][1]} km/h")

    print("\n[3/3] Validating driver-to-driver pairwise synchronization...")
    p1 = validate_pair("LEC vs MAG", "LEC", "MAG", raw_data["LEC"], raw_data["MAG"], target_hz=25.0)
    p2 = validate_pair("LEC vs SAI", "LEC", "SAI", raw_data["LEC"], raw_data["SAI"], target_hz=25.0)
    p3 = validate_pair("MAG vs GAS", "MAG", "GAS", raw_data["MAG"], raw_data["GAS"], target_hz=25.0)

    print("\n" + "=" * 70)
    print(f"ALL PREPROCESSING & SYNCHRONIZATION INVARIANTS PASSED! (v={PREPROCESSING_VERSION})")
    print("=" * 70)


if __name__ == "__main__":
    run_monza_real_validation()
