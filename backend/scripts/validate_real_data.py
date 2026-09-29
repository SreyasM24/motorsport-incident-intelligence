"""Validation script for real FastF1 (2024 Monza Race) and OpenF1 live feeds.

Tests real ingestion, data normalization, cache performance, channel integrity,
and invariant assertions.
"""

import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import logger
from app.data.fastf1.loader import FastF1DataSource
from app.data.fastf1.cache import get_cache_status
from app.data.openf1.client import OpenF1Client
from app.data.openf1.normalizer import (
    normalize_openf1_session,
    normalize_openf1_driver,
    normalize_openf1_car_data,
    normalize_openf1_race_control,
)


def validate_fastf1_monza():
    """Run real FastF1 validation against 2024 Italian Grand Prix Race."""
    print("=" * 60)
    print("STARTING FASTF1 REAL DATA VALIDATION: 2024 Monza Grand Prix")
    print("=" * 60)

    start_time = time.time()
    source = FastF1DataSource()

    # 1. Event Loading
    t0 = time.time()
    event = source.get_event(2024, "Monza")
    t_event = time.time() - t0
    print(f"[FASTF1] Event loaded in {t_event:.2f}s: {event.name} ({event.circuit_name}, {event.country})")
    assert event.name == "Italian Grand Prix"
    assert "Monza" in event.circuit_name
    assert event.country == "Italy"

    # 2. Session Loading
    t0 = time.time()
    session = source.get_session(2024, "Monza", "Race")
    t_session = time.time() - t0
    print(f"[FASTF1] Session loaded in {t_session:.2f}s: {session.session_name} ({session.session_type})")
    assert session.session_type == "Race"
    assert session.id.startswith("f1-2024")

    # 3. Driver Discovery
    t0 = time.time()
    drivers = source.get_session_drivers(2024, "Monza", "Race")
    t_drivers = time.time() - t0
    print(f"[FASTF1] Drivers discovered in {t_drivers:.2f}s: {len(drivers)} drivers")
    assert len(drivers) >= 20, f"Expected at least 20 drivers, got {len(drivers)}"

    driver_codes = {d.code for d in drivers}
    print(f"[FASTF1] Sample drivers: {sorted(list(driver_codes))[:8]}")
    assert "VER" in driver_codes, "Max Verstappen (VER) not found"
    assert "LEC" in driver_codes, "Charles Leclerc (LEC) not found"
    assert "NOR" in driver_codes, "Lando Norris (NOR) not found"

    # Verify driver mapping
    lec = next(d for d in drivers if d.code == "LEC")
    print(f"[FASTF1] Driver verification: Code={lec.code}, Number={lec.number}, Name={lec.full_name}, Team={lec.team}, Color={lec.team_color}")
    assert lec.number == 16
    assert "Ferrari" in lec.team

    # 4. Lap Association
    t0 = time.time()
    laps = source.get_session_laps(2024, "Monza", "Race", driver="LEC")
    t_laps = time.time() - t0
    print(f"[FASTF1] Laps retrieved for LEC in {t_laps:.2f}s: {len(laps)} laps")
    assert len(laps) > 0, "No laps retrieved for Charles Leclerc"
    sample_lap = laps[0]
    print(f"[FASTF1] Sample Lap 1: LapTime={sample_lap.lap_time_seconds}s, S1={sample_lap.sector_1_seconds}s, S2={sample_lap.sector_2_seconds}s, S3={sample_lap.sector_3_seconds}s, Compound={sample_lap.compound}")
    assert sample_lap.lap_number == 1

    # 5. Telemetry Loading & Channel Inspection
    t0 = time.time()
    # Test bounded lap telemetry (Lap 10 of Charles Leclerc)
    telemetry = source.get_driver_telemetry(2024, "Monza", "Race", driver="LEC", lap=10)
    t_tel = time.time() - t0
    print(f"[FASTF1] Telemetry points for LEC Lap 10 loaded in {t_tel:.2f}s: {len(telemetry)} points")
    assert len(telemetry) > 0, "Telemetry rows count is 0"

    pt0 = telemetry[0]
    mid_pt = telemetry[len(telemetry) // 2]
    print(f"[FASTF1] Telemetry Sample (Mid-Lap): TimeOffset={mid_pt.time_offset}s, Speed={mid_pt.speed} km/h, Throttle={mid_pt.throttle}%, Brake={mid_pt.brake}%, Gear={mid_pt.gear}, RPM={mid_pt.rpm}, Pos=({mid_pt.x}, {mid_pt.y}, {mid_pt.z})")

    # Invariant assertions
    assert mid_pt.timestamp is not None, "Timestamp is missing"
    assert mid_pt.speed is not None and mid_pt.speed > 0, "Speed channel is missing or 0"
    assert mid_pt.x is not None and mid_pt.y is not None, "Spatial coordinate channels (X, Y) are missing"
    assert mid_pt.throttle is not None, "Throttle channel is missing"
    assert mid_pt.steering is None, "Steering should be None (unavailable in FastF1)"

    # 6. Cache Verification on Repeated Access
    t0 = time.time()
    telemetry_cached = source.get_driver_telemetry(2024, "Monza", "Race", driver="LEC", lap=10)
    t_cached = time.time() - t0
    print(f"[FASTF1] Repeated access loaded in {t_cached:.4f}s (Cache Speedup: {t_tel / max(t_cached, 0.0001):.1f}x)")
    assert len(telemetry_cached) == len(telemetry)

    cache_stat = get_cache_status()
    print(f"[FASTF1] Cache Status: Path={cache_stat['path']}, Files={cache_stat['file_count']}, Size={cache_stat['size_mb']} MB")
    assert cache_stat["exists"] is True
    assert cache_stat["file_count"] > 0

    total_fastf1_time = time.time() - start_time
    print(f"[FASTF1] ALL MONZA 2024 INVARIANTS PASSED in {total_fastf1_time:.2f}s\n")
    return {
        "event_name": event.name,
        "circuit": event.circuit_name,
        "drivers_count": len(drivers),
        "sample_lap_count": len(laps),
        "telemetry_points_lap10": len(telemetry),
        "cache_files": cache_stat["file_count"],
        "cache_size_mb": cache_stat["size_mb"],
        "fastf1_time": total_fastf1_time,
    }


def validate_openf1_live():
    """Run bounded live validation against OpenF1 API."""
    print("=" * 60)
    print("STARTING OPENF1 BOUNDED LIVE VALIDATION")
    print("=" * 60)

    start_time = time.time()
    client = OpenF1Client(timeout=15.0)

    # 1. Session Lookup (2024 Italy)
    t0 = time.time()
    sessions = client.get_sessions(year=2024, country_name="Italy")
    t_sess = time.time() - t0
    print(f"[OPENF1] Sessions retrieved in {t_sess:.2f}s: {len(sessions)} sessions")
    assert len(sessions) > 0, "No OpenF1 sessions found for 2024 Italy"

    race_sess = next((s for s in sessions if "Race" in str(s.get("session_name"))), sessions[0])
    session_key = race_sess["session_key"]
    print(f"[OPENF1] Selected session: Key={session_key}, Name={race_sess.get('session_name')}, Circuit={race_sess.get('circuit_short_name')}")

    norm_session = normalize_openf1_session(race_sess)
    print(f"[OPENF1] Normalized Session: ID={norm_session.id}, Name={norm_session.session_name}, Type={norm_session.session_type}")
    assert norm_session.source == "openf1"
    assert norm_session.source_id == str(session_key)

    # 2. Driver Lookup for Selected Session
    t0 = time.time()
    drivers_data = client.get_drivers(session_key=session_key)
    t_drv = time.time() - t0
    print(f"[OPENF1] Drivers retrieved in {t_drv:.2f}s: {len(drivers_data)} drivers")
    assert len(drivers_data) > 0, "No drivers returned for session"

    sample_d = drivers_data[0]
    norm_driver = normalize_openf1_driver(sample_d, session_id=norm_session.id)
    print(f"[OPENF1] Sample Driver: Code={norm_driver.code}, Number={norm_driver.number}, Name={norm_driver.full_name}, Team={norm_driver.team}")
    assert norm_driver.code is not None and len(norm_driver.code) > 0

    # 3. Bounded Car Telemetry Lookup (Driver 16, limit 50)
    target_drv_num = sample_d.get("driver_number", 16)
    t0 = time.time()
    car_points = client.get_car_data(session_key=session_key, driver_number=target_drv_num, limit=50)
    t_car = time.time() - t0
    print(f"[OPENF1] Bounded Car Data (limit 50) retrieved in {t_car:.2f}s: {len(car_points)} points")
    assert len(car_points) > 0, "No car_data points returned"

    # 4. Bounded Location Lookup (same driver, limit 50)
    t0 = time.time()
    loc_points = client.get_location(session_key=session_key, driver_number=target_drv_num, limit=50)
    t_loc = time.time() - t0
    print(f"[OPENF1] Bounded Location Data (limit 50) retrieved in {t_loc:.2f}s: {len(loc_points)} points")

    # 5. Normalization into Canonical Telemetry Stream
    norm_telemetry = normalize_openf1_car_data(car_points, location_points=loc_points, driver_code=norm_driver.code)
    print(f"[OPENF1] Normalized {len(norm_telemetry)} telemetry points")
    sample_pt = norm_telemetry[0]
    print(f"[OPENF1] Sample Point: TimeOffset={sample_pt.time_offset}s, Speed={sample_pt.speed} km/h, RPM={sample_pt.rpm}, Gear={sample_pt.gear}, Throttle={sample_pt.throttle}%, Brake={sample_pt.brake}%")
    assert sample_pt.speed is not None
    assert sample_pt.steering is None  # OpenF1 does not provide steering

    # 6. Race Control Messages
    t0 = time.time()
    rc_msgs = client.get_race_control_messages(session_key=session_key)
    t_rc = time.time() - t0
    print(f"[OPENF1] Race Control messages retrieved in {t_rc:.2f}s: {len(rc_msgs)} messages")
    if rc_msgs:
        sample_rc = normalize_openf1_race_control(rc_msgs[0])
        print(f"[OPENF1] Sample RC Message: Category={sample_rc.category}, Message='{sample_rc.message[:60]}...'")

    client.close()
    total_openf1_time = time.time() - start_time
    print(f"[OPENF1] ALL OPENF1 INVARIANTS PASSED in {total_openf1_time:.2f}s\n")
    return {
        "session_key": session_key,
        "session_name": race_sess.get("session_name"),
        "drivers_count": len(drivers_data),
        "telemetry_points_sample": len(norm_telemetry),
        "race_control_messages_count": len(rc_msgs),
        "openf1_time": total_openf1_time,
    }


if __name__ == "__main__":
    fastf1_res = validate_fastf1_monza()
    openf1_res = validate_openf1_live()
    print("=" * 60)
    print("ALL REAL MOTORSPORT DATA VALIDATIONS SUCCESSFUL!")
    print("=" * 60)
