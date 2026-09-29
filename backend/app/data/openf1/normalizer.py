"""OpenF1 data normalization module.

Converts OpenF1 JSON payloads into canonical internal domain objects.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from app.data.domain import (
    NormalizedRace,
    NormalizedSession,
    NormalizedDriver,
    NormalizedLap,
    NormalizedTelemetryPoint,
    NormalizedRaceControlMessage,
)
from app.data.fastf1.normalizer import slugify


def _parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Safely parse an ISO-8601 datetime string."""
    if not dt_str:
        return None
    try:
        # Handle trailing Z or offsets
        clean_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None


def normalize_openf1_session(s: Dict[str, Any]) -> NormalizedSession:
    """Normalize OpenF1 session dictionary into NormalizedSession."""
    session_key = str(s.get("session_key", ""))
    year = s.get("year", 2024)
    country_name = str(s.get("country_name", "Grand Prix"))
    circuit_short_name = str(s.get("circuit_short_name", country_name))
    session_name = str(s.get("session_name", "Race"))
    session_type = str(s.get("session_type", session_name))

    date_start_str = s.get("date_start")
    date_end_str = s.get("date_end")
    start_time = _parse_iso_datetime(date_start_str)
    end_time = _parse_iso_datetime(date_end_str)
    session_date = start_time.date() if start_time else None

    race_slug = slugify(country_name)
    race_id = f"f1-{year}-{race_slug}"
    session_slug = slugify(session_name)
    session_id = f"{race_id}-{session_slug}"

    return NormalizedSession(
        id=session_id,
        race_id=race_id,
        session_type=session_type,
        session_name=f"{country_name} {session_name}",
        session_date=session_date,
        start_time=start_time,
        end_time=end_time,
        total_laps=None,
        status="ANALYSIS_READY",
        source="openf1",
        source_id=session_key,
        metadata={
            "session_key": session_key,
            "circuit_key": s.get("circuit_key"),
            "circuit_short_name": circuit_short_name,
            "location": s.get("location"),
            "gmt_offset": s.get("gmt_offset"),
        },
    )


def normalize_openf1_driver(d: Dict[str, Any], session_id: str) -> NormalizedDriver:
    """Normalize OpenF1 driver dictionary into NormalizedDriver."""
    driver_number = int(d.get("driver_number", 0))
    code = str(d.get("name_acronym", str(driver_number))).strip().upper()
    full_name = str(d.get("full_name", d.get("broadcast_name", code)))
    first_name = d.get("first_name")
    last_name = d.get("last_name")
    team = str(d.get("team_name", "Unknown Team"))

    team_colour = d.get("team_colour")
    team_color = None
    if team_colour:
        col = str(team_colour).strip()
        team_color = f"#{col}" if not col.startswith("#") else col

    nationality = d.get("country_code")
    driver_id = f"{session_id}-{code.lower()}" if code else f"{session_id}-{driver_number}"

    return NormalizedDriver(
        id=driver_id,
        session_id=session_id,
        code=code,
        number=driver_number,
        full_name=full_name,
        first_name=str(first_name) if first_name else None,
        last_name=str(last_name) if last_name else None,
        abbreviation=code,
        team=team,
        team_color=team_color,
        nationality=str(nationality) if nationality else None,
        laps_completed=0,
        source="openf1",
        source_id=str(driver_number),
    )


def normalize_openf1_lap(l: Dict[str, Any], driver_code: str = "") -> NormalizedLap:
    """Normalize OpenF1 lap dictionary into NormalizedLap."""
    driver_number = int(l.get("driver_number", 0))
    lap_number = int(l.get("lap_number", 0))

    def _sec(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            return round(float(val), 3)
        except (ValueError, TypeError):
            return None

    lap_time = _sec(l.get("lap_duration"))
    s1 = _sec(l.get("duration_sector_1"))
    s2 = _sec(l.get("duration_sector_2"))
    s3 = _sec(l.get("duration_sector_3"))

    start_time = _parse_iso_datetime(l.get("date_start"))
    is_pit_out = bool(l.get("is_pit_out_lap", False))

    return NormalizedLap(
        driver_code=driver_code,
        driver_number=driver_number,
        lap_number=lap_number,
        lap_time_seconds=lap_time,
        sector_1_seconds=s1,
        sector_2_seconds=s2,
        sector_3_seconds=s3,
        compound=None,
        is_valid=not is_pit_out,
        start_time=start_time,
        source="openf1",
    )


def normalize_openf1_car_data(
    car_points: List[Dict[str, Any]],
    location_points: Optional[List[Dict[str, Any]]] = None,
    driver_code: str = "",
) -> List[NormalizedTelemetryPoint]:
    """Normalize OpenF1 car_data and optional location records into NormalizedTelemetryPoint stream.

    Preserves raw observations and timestamps without artificial resampling.
    """
    loc_by_date = {}
    if location_points:
        for loc in location_points:
            d_str = loc.get("date")
            if d_str:
                loc_by_date[d_str] = loc

    points: List[NormalizedTelemetryPoint] = []
    base_time = None

    for item in car_points:
        date_str = item.get("date")
        dt = _parse_iso_datetime(date_str)

        time_offset = 0.0
        if dt:
            if base_time is None:
                base_time = dt
            time_offset = round((dt - base_time).total_seconds(), 4)

        drv_num = item.get("driver_number")

        # Extract spatial location if available
        x = y = z = None
        if date_str in loc_by_date:
            loc = loc_by_date[date_str]
            x = loc.get("x")
            y = loc.get("y")
            z = loc.get("z")

        speed = float(item["speed"]) if item.get("speed") is not None else None
        throttle = float(item["throttle"]) if item.get("throttle") is not None else None

        brake_raw = item.get("brake")
        brake = float(brake_raw) if brake_raw is not None else None
        if brake is not None and brake <= 1.0 and brake > 0:
            brake = 100.0

        gear = int(item["n_gear"]) if item.get("n_gear") is not None else None
        rpm = int(item["rpm"]) if item.get("rpm") is not None else None
        drs = int(item["drs"]) if item.get("drs") is not None else None

        points.append(
            NormalizedTelemetryPoint(
                timestamp=dt,
                time_offset=time_offset,
                driver_code=driver_code,
                driver_number=int(drv_num) if drv_num is not None else None,
                lap_number=None,
                distance=None,
                x=round(float(x) / 10.0, 3) if x is not None else None,
                y=round(float(y) / 10.0, 3) if y is not None else None,
                z=round(float(z) / 10.0, 3) if z is not None else None,
                speed=speed,
                throttle=throttle,
                brake=brake,
                steering=None,  # OpenF1 does not provide steering angle
                gear=gear,
                rpm=rpm,
                drs=drs,
                accel_x=None,
                accel_y=None,
                source="openf1",
            )
        )

    return points


def normalize_openf1_race_control(msg: Dict[str, Any]) -> NormalizedRaceControlMessage:
    """Normalize OpenF1 race_control record into NormalizedRaceControlMessage."""
    dt = _parse_iso_datetime(msg.get("date"))
    lap_num = msg.get("lap_number")

    sector_raw = msg.get("sector")
    sector = None
    if sector_raw is not None:
        try:
            sector = int(sector_raw)
        except (ValueError, TypeError):
            pass

    return NormalizedRaceControlMessage(
        timestamp=dt,
        lap_number=int(lap_num) if lap_num is not None else None,
        category=msg.get("category"),
        message=str(msg.get("message", "")),
        flag=msg.get("flag"),
        scope=msg.get("scope"),
        sector=sector,
        source="openf1",
    )
