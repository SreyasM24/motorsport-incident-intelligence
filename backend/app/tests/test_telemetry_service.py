"""Deterministic unit tests for telemetry preprocessing, resampling, and pair synchronization."""

from datetime import datetime, timezone, timedelta
import numpy as np
import pytest

from app.data.domain import NormalizedTelemetryPoint
from app.services.telemetry_service import (
    clean_and_sort_driver_telemetry,
    resample_driver_stream,
    calculate_closing_speeds,
    synchronize_pair,
    ensure_utc,
    PREPROCESSING_VERSION,
)


def make_sample_point(
    offset_sec: float,
    speed: float = 200.0,
    throttle: float = 100.0,
    brake: float = 0.0,
    gear: int = 6,
    x: float = 1000.0,
    y: float = 2000.0,
    z: float = 100.0,
    lap: int = 10,
    driver: str = "LEC",
) -> NormalizedTelemetryPoint:
    """Helper to synthesize test observation frames with explicit UTC timestamps."""
    base_time = datetime(2024, 9, 1, 13, 0, 0, tzinfo=timezone.utc)
    ts = base_time + timedelta(seconds=offset_sec)
    return NormalizedTelemetryPoint(
        timestamp=ts,
        time_offset=offset_sec,
        driver_code=driver,
        driver_number=16 if driver == "LEC" else 20,
        lap_number=lap,
        distance=offset_sec * 50.0,
        x=x,
        y=y,
        z=z,
        speed=speed,
        throttle=throttle,
        brake=brake,
        gear=gear,
        rpm=11000,
        drs=0,
        source="test",
    )


def test_clean_and_sort_monotonic():
    """Verify clean_and_sort enforces monotonic timestamp ordering."""
    p1 = make_sample_point(offset_sec=2.0)
    p2 = make_sample_point(offset_sec=1.0)
    p3 = make_sample_point(offset_sec=3.0)

    cleaned = clean_and_sort_driver_telemetry([p1, p2, p3])
    assert len(cleaned) == 3
    assert cleaned[0].time_offset == 1.0
    assert cleaned[1].time_offset == 2.0
    assert cleaned[2].time_offset == 3.0


def test_clean_and_sort_duplicate_timestamps():
    """Verify duplicate timestamps are deterministically aggregated without data loss."""
    # Two observations at exact same timestamp with differing channels
    p1 = make_sample_point(offset_sec=5.0, speed=200.0, gear=5)
    p2 = make_sample_point(offset_sec=5.0, speed=220.0, gear=6)

    cleaned = clean_and_sort_driver_telemetry([p1, p2])
    assert len(cleaned) == 1
    # Continuous speed averaged: (200 + 220) / 2 = 210.0
    assert cleaned[0].speed == 210.0
    # Discrete gear takes last observed state: 6
    assert cleaned[0].gear == 6


def test_resample_driver_stream_linear_interpolation():
    """Verify continuous channels are linearly interpolated on the uniform grid."""
    # Observations at t=0.0s (speed=100) and t=1.0s (speed=200)
    p0 = make_sample_point(offset_sec=0.0, speed=100.0, throttle=50.0, x=0.0)
    p1 = make_sample_point(offset_sec=1.0, speed=200.0, throttle=100.0, x=100.0)

    # Resample at 10 Hz (step = 0.1s)
    resampled = resample_driver_stream([p0, p1], frequency_hz=10.0)
    assert len(resampled) == 11  # 0.0 to 1.0 inclusive at 0.1s step

    # At midpoint t=0.5s: speed should be exactly 150.0
    mid = resampled[5]
    assert round(mid.time_offset, 2) == 0.50
    assert mid.speed == 150.0
    assert mid.throttle == 75.0
    assert mid.x == 50.0


def test_resample_driver_stream_discrete_channels():
    """Verify discrete channels (gear, drs, lap) are nearest/forward-filled, not averaged."""
    p0 = make_sample_point(offset_sec=0.0, gear=3, lap=10)
    p1 = make_sample_point(offset_sec=1.0, gear=4, lap=10)

    resampled = resample_driver_stream([p0, p1], frequency_hz=10.0)
    # Check that all gear values are discrete integers (3 or 4), never floats like 3.5
    for pt in resampled:
        assert pt.gear in (3, 4)
        assert isinstance(pt.gear, int)
        assert pt.lap_number == 10


def test_resample_driver_stream_max_gap_policy():
    """Verify gaps exceeding max_gap_seconds are preserved as None/missing."""
    # Data from 0.0s to 1.0s, then a 5-second blackout until 6.0s
    p0 = make_sample_point(offset_sec=0.0, speed=200.0)
    p1 = make_sample_point(offset_sec=1.0, speed=205.0)
    p2 = make_sample_point(offset_sec=6.0, speed=210.0)
    p3 = make_sample_point(offset_sec=7.0, speed=215.0)

    # Max gap allowed = 1.0 second
    resampled = resample_driver_stream([p0, p1, p2, p3], frequency_hz=1.0, max_gap_seconds=1.0)
    # At t=3.0s (in the gap between 1.0 and 6.0), speed should be None (MISSING)
    pt_in_gap = next(pt for pt in resampled if round(pt.time_offset, 1) == 3.0)
    assert pt_in_gap.speed is None
    assert pt_in_gap.provenance.get("speed") == "MISSING"


def test_calculate_closing_speeds():
    """Verify closing speed calculation: -d(gap)/dt in m/s."""
    dt = 0.04  # 25 Hz
    # Distance shrinking by 1.0 meter per 0.04s step -> closing speed = +25.0 m/s
    gaps = np.array([100.0, 99.0, 98.0, 97.0, 96.0])
    closing = calculate_closing_speeds(gaps, dt_sec=dt)

    assert len(closing) == len(gaps)
    # Central derivative for midpoints: -(98 - 100) / (2 * 0.04) = 2.0 / 0.08 = 25.0
    assert np.isclose(closing[2], 25.0, atol=0.1)

    # Distance opening by 1.0 meter per step -> closing speed = -25.0 m/s
    gaps_opening = np.array([50.0, 51.0, 52.0, 53.0, 54.0])
    closing_opening = calculate_closing_speeds(gaps_opening, dt_sec=dt)
    assert np.isclose(closing_opening[2], -25.0, atol=0.1)


def test_synchronize_pair_euclidean_gap_and_delta():
    """Verify pair synchronization computes speed differences and 3D Euclidean gap."""
    # Driver A: moving along X axis from X=0 to X=100
    points_a = [
        make_sample_point(offset_sec=0.0, speed=200.0, x=0.0, y=0.0, z=0.0, lap=12, driver="LEC"),
        make_sample_point(offset_sec=1.0, speed=220.0, x=100.0, y=0.0, z=0.0, lap=12, driver="LEC"),
    ]
    # Driver B: moving along X axis, 30m behind (X=-30 to X=70)
    points_b = [
        make_sample_point(offset_sec=0.0, speed=180.0, x=-30.0, y=0.0, z=0.0, lap=11, driver="MAG"),
        make_sample_point(offset_sec=1.0, speed=210.0, x=70.0, y=0.0, z=0.0, lap=11, driver="MAG"),
    ]

    synced = synchronize_pair(points_a, points_b, frequency_hz=25.0)
    assert len(synced) > 0

    mid = synced[len(synced) // 2]
    # Speed difference = speed_a - speed_b
    assert mid.speed_difference > 0
    # Euclidean gap should remain approximately 30 meters
    assert np.isclose(mid.gap_meters, 30.0, atol=1.0)
    # Lap numbers preserved independently
    assert mid.lap_number_a == 12
    assert mid.lap_number_b == 11
    # Different laps detected
    assert mid.same_lap is False


def test_calculate_closing_speeds_nan_safe_no_mach30_spikes():
    """Verify missing/NaN gap observations do not generate artificial Mach 30 spikes."""
    dt = 0.04  # 25 Hz
    # Array with a gap blackout in the middle
    gaps = np.array([100.0, 99.0, 98.0, np.nan, np.nan, 20.0, 19.0, 18.0])
    closing = calculate_closing_speeds(gaps, dt_sec=dt)

    assert len(closing) == len(gaps)
    # Valid segments have correct continuous derivative: -(98 - 100) / (2 * 0.04) = +25.0 m/s
    assert np.isclose(closing[1], 25.0, atol=0.1)
    # The point right before the blackout (index 2) uses backward difference: -(98 - 99) / 0.04 = +25.0 m/s
    assert np.isclose(closing[2], 25.0, atol=0.1)
    # Missing points must be NaN, NEVER an artificial spike of thousands of m/s
    assert np.isnan(closing[3])
    assert np.isnan(closing[4])
    # The point right after the blackout (index 5) uses forward difference: -(19 - 20) / 0.04 = +25.0 m/s
    assert np.isclose(closing[5], 25.0, atol=0.1)
    # Valid interior point on second segment
    assert np.isclose(closing[6], 25.0, atol=0.1)


def test_physical_validation_helpers():
    """Verify physical sanity bounds validation for speed, throttle, brake, position, and closing speed."""
    from app.services.telemetry_service import (
        validate_speed,
        validate_throttle,
        validate_brake,
        validate_position,
        validate_closing_speed,
    )

    # Speed bounds [0, 420] km/h
    assert validate_speed(-15.0) == 0.0
    assert validate_speed(315.4) == 315.4
    assert validate_speed(500.0) == 420.0
    assert validate_speed(None) is None

    # Throttle and Brake [0, 100]%
    assert validate_throttle(120.0) == 100.0
    assert validate_throttle(-10.0) == 0.0
    assert validate_throttle(85.5) == 85.5
    assert validate_brake(105.0) == 100.0
    assert validate_brake(-2.0) == 0.0

    # Spatial Position bounding
    x, y, z = validate_position(1200.0, -800.0, 15.0)
    assert x == 1200.0 and y == -800.0 and z == 15.0
    # Hyperspace coordinates outside circuit radius rejected
    x_bad, y_bad, z_bad = validate_position(999999.0, 0.0, 0.0)
    assert x_bad is None and y_bad is None and z_bad is None

    # Kinematic closing speed bounded by |v_a| + |v_b|
    # At 180 km/h (50 m/s) and 180 km/h (50 m/s), kinematic limit is ~105 m/s
    bounded_closing = validate_closing_speed(300.0, speed_a_kmh=180.0, speed_b_kmh=180.0)
    assert bounded_closing <= 106.0
    # Physically normal closing speed unchanged
    normal_closing = validate_closing_speed(15.5, speed_a_kmh=300.0, speed_b_kmh=280.0)
    assert normal_closing == 15.5


def test_synchronize_pair_same_lap_flag():
    """Verify same_lap flag is True when lap numbers match and False when differing."""
    # Same lap (lap 15)
    points_a1 = [
        make_sample_point(offset_sec=0.0, speed=200.0, x=0.0, y=0.0, z=0.0, lap=15, driver="VER"),
        make_sample_point(offset_sec=1.0, speed=220.0, x=50.0, y=0.0, z=0.0, lap=15, driver="VER"),
    ]
    points_b1 = [
        make_sample_point(offset_sec=0.0, speed=190.0, x=-20.0, y=0.0, z=0.0, lap=15, driver="NOR"),
        make_sample_point(offset_sec=1.0, speed=210.0, x=30.0, y=0.0, z=0.0, lap=15, driver="NOR"),
    ]
    synced_same = synchronize_pair(points_a1, points_b1, frequency_hz=25.0)
    assert all(pt.same_lap is True for pt in synced_same)

    # Different laps (lap 15 vs lap 14)
    points_b2 = [
        make_sample_point(offset_sec=0.0, speed=190.0, x=-20.0, y=0.0, z=0.0, lap=14, driver="NOR"),
        make_sample_point(offset_sec=1.0, speed=210.0, x=30.0, y=0.0, z=0.0, lap=14, driver="NOR"),
    ]
    synced_diff = synchronize_pair(points_a1, points_b2, frequency_hz=25.0)
    assert all(pt.same_lap is False for pt in synced_diff)

