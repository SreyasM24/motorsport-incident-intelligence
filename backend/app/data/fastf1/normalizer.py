"""FastF1 data normalization module.

Converts raw FastF1 DataFrames and Series into canonical internal domain objects
without leaking pandas dataframes into the application core.
"""

import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np

from app.data.domain import (
    NormalizedRace,
    NormalizedSession,
    NormalizedDriver,
    NormalizedLap,
    NormalizedTelemetryPoint,
)


def slugify(text: str) -> str:
    """Convert text into a URL and ID friendly slug."""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


def normalize_fastf1_event(event_data: Union[pd.Series, dict], season: int) -> NormalizedRace:
    """Normalize a FastF1 event (schedule row) into NormalizedRace."""
    if isinstance(event_data, pd.Series):
        event_dict = event_data.to_dict()
    else:
        event_dict = dict(event_data)

    event_name = str(event_dict.get("EventName", "Grand Prix"))
    official_name = event_dict.get("OfficialEventName")
    if pd.isna(official_name):
        official_name = event_name
    else:
        official_name = str(official_name)

    country = str(event_dict.get("Country", "Unknown"))
    location = event_dict.get("Location")
    city = str(location) if location and not pd.isna(location) else None

    # Circuit name fallback to location or event name
    circuit_name = f"{city} Circuit" if city else f"{event_name} Circuit"
    if "monza" in event_name.lower() or (city and "monza" in city.lower()):
        circuit_name = "Autodromo Nazionale Monza"
    elif "silverstone" in event_name.lower():
        circuit_name = "Silverstone Circuit"
    elif "spa" in event_name.lower():
        circuit_name = "Circuit de Spa-Francorchamps"
    elif "monaco" in event_name.lower():
        circuit_name = "Circuit de Monaco"

    round_raw = event_dict.get("RoundNumber")
    round_number = None
    if round_raw is not None and not pd.isna(round_raw):
        try:
            round_number = int(round_raw)
        except (ValueError, TypeError):
            pass

    event_date_raw = event_dict.get("EventDate")
    event_date = None
    if event_date_raw is not None and not pd.isna(event_date_raw):
        if isinstance(event_date_raw, pd.Timestamp):
            event_date = event_date_raw.date()
        elif isinstance(event_date_raw, datetime):
            event_date = event_date_raw.date()
        elif isinstance(event_date_raw, str):
            try:
                event_date = datetime.fromisoformat(event_date_raw).date()
            except ValueError:
                pass

    slug = slugify(event_name)
    event_id = f"f1-{season}-{slug}" if slug else f"f1-{season}-round-{round_number}"

    return NormalizedRace(
        id=event_id,
        series="Formula 1",
        season=str(season),
        round_number=round_number,
        name=event_name,
        official_name=official_name,
        circuit_name=circuit_name,
        country=country,
        city=city,
        event_date=event_date,
        source="fastf1",
        source_id=str(round_number) if round_number is not None else slug,
        metadata={
            "event_format": str(event_dict.get("EventFormat", "conventional")),
            "f1_api_support": bool(event_dict.get("F1ApiSupport", True)),
        },
    )


def normalize_fastf1_session(
    session_obj: Any,
    season: int,
    race_id: str,
) -> NormalizedSession:
    """Normalize a FastF1 Session object into NormalizedSession."""
    session_name = getattr(session_obj, "name", "Race")
    event = getattr(session_obj, "event", None)

    session_type_map = {
        "Practice 1": "Practice 1",
        "Practice 2": "Practice 2",
        "Practice 3": "Practice 3",
        "Qualifying": "Qualifying",
        "Sprint": "Sprint",
        "Sprint Shootout": "Sprint Shootout",
        "Sprint Qualifying": "Sprint Qualifying",
        "Race": "Race",
    }
    session_type = session_type_map.get(session_name, session_name)

    session_date_raw = getattr(session_obj, "date", None)
    session_date = None
    start_time = None
    if session_date_raw is not None and not pd.isna(session_date_raw):
        if isinstance(session_date_raw, pd.Timestamp):
            start_time = session_date_raw.to_pydatetime()
            session_date = session_date_raw.date()
        elif isinstance(session_date_raw, datetime):
            start_time = session_date_raw
            session_date = session_date_raw.date()

    total_laps = None
    try:
        if hasattr(session_obj, "total_laps") and session_obj.total_laps:
            total_laps = int(session_obj.total_laps)
        elif hasattr(session_obj, "laps") and session_obj.laps is not None and not session_obj.laps.empty:
            total_laps = int(session_obj.laps["LapNumber"].max())
    except Exception:
        pass

    session_slug = slugify(session_type)
    session_id = f"{race_id}-{session_slug}"

    return NormalizedSession(
        id=session_id,
        race_id=race_id,
        session_type=session_type,
        session_name=f"{getattr(event, 'EventName', 'Grand Prix')} {session_name}",
        session_date=session_date,
        start_time=start_time,
        end_time=None,
        total_laps=total_laps,
        status="ANALYSIS_READY",
        source="fastf1",
        source_id=f"{season}_{race_id}_{session_slug}",
    )


def normalize_fastf1_driver(
    driver_row: Union[pd.Series, dict],
    session_id: str,
    laps_df: Optional[pd.DataFrame] = None,
) -> NormalizedDriver:
    """Normalize a FastF1 driver result row into NormalizedDriver."""
    if isinstance(driver_row, pd.Series):
        d = driver_row.to_dict()
    else:
        d = dict(driver_row)

    code = str(d.get("Abbreviation", "")).strip().upper()
    number_raw = d.get("DriverNumber", 0)
    try:
        number = int(number_raw)
    except (ValueError, TypeError):
        number = 0

    full_name = str(d.get("FullName", code))
    first_name = d.get("FirstName")
    last_name = d.get("LastName")
    team = str(d.get("TeamName", "Unknown Team"))

    team_color_raw = d.get("TeamColor")
    team_color = None
    if team_color_raw and not pd.isna(team_color_raw):
        color_str = str(team_color_raw).strip()
        team_color = f"#{color_str}" if not color_str.startswith("#") else color_str

    nationality = d.get("CountryCode")
    nationality_str = str(nationality) if nationality and not pd.isna(nationality) else None

    # Calculate session performance metrics from laps if provided
    laps_completed = 0
    max_speed_kmh = None
    avg_speed_kmh = None

    if laps_df is not None and not laps_df.empty:
        driver_laps = laps_df[
            (laps_df["Driver"] == code) | (laps_df["DriverNumber"] == str(number))
        ]
        if not driver_laps.empty:
            laps_completed = int(driver_laps["LapNumber"].nunique())
            speeds = []
            for speed_col in ["SpeedST", "SpeedFL", "SpeedI1", "SpeedI2"]:
                if speed_col in driver_laps.columns:
                    valid_speeds = driver_laps[speed_col].dropna()
                    if not valid_speeds.empty:
                        speeds.extend(valid_speeds.tolist())
            if speeds:
                max_speed_kmh = round(float(np.nanmax(speeds)), 1)
                avg_speed_kmh = round(float(np.nanmean(speeds)), 1)

    driver_id = f"{session_id}-{code.lower()}" if code else f"{session_id}-{number}"

    return NormalizedDriver(
        id=driver_id,
        session_id=session_id,
        code=code,
        number=number,
        full_name=full_name,
        first_name=str(first_name) if first_name and not pd.isna(first_name) else None,
        last_name=str(last_name) if last_name and not pd.isna(last_name) else None,
        abbreviation=code,
        team=team,
        team_color=team_color,
        nationality=nationality_str,
        laps_completed=laps_completed,
        avg_speed_kmh=avg_speed_kmh,
        max_speed_kmh=max_speed_kmh,
        source="fastf1",
        source_id=str(d.get("DriverId", code)),
    )


def normalize_fastf1_lap(lap_row: Union[pd.Series, dict], driver_code: str, driver_number: int) -> NormalizedLap:
    """Normalize a FastF1 lap record into NormalizedLap."""
    if isinstance(lap_row, pd.Series):
        d = lap_row.to_dict()
    else:
        d = dict(lap_row)

    lap_number = int(d.get("LapNumber", 0))

    def _to_sec(val: Any) -> Optional[float]:
        if val is None or pd.isna(val):
            return None
        if isinstance(val, (timedelta, pd.Timedelta)):
            return round(val.total_seconds(), 3)
        try:
            return round(float(val), 3)
        except (ValueError, TypeError):
            return None

    lap_time = _to_sec(d.get("LapTime"))
    s1 = _to_sec(d.get("Sector1Time"))
    s2 = _to_sec(d.get("Sector2Time"))
    s3 = _to_sec(d.get("Sector3Time"))

    compound = d.get("Compound")
    compound_str = str(compound) if compound and not pd.isna(compound) else None

    deleted = bool(d.get("Deleted", False))
    accurate = bool(d.get("IsAccurate", True))
    is_valid = not deleted and accurate

    start_time = None
    start_time_raw = d.get("LapStartDate")
    if start_time_raw is not None and not pd.isna(start_time_raw):
        if isinstance(start_time_raw, pd.Timestamp):
            start_time = start_time_raw.to_pydatetime()
        elif isinstance(start_time_raw, datetime):
            start_time = start_time_raw

    return NormalizedLap(
        driver_code=driver_code,
        driver_number=driver_number,
        lap_number=lap_number,
        lap_time_seconds=lap_time,
        sector_1_seconds=s1,
        sector_2_seconds=s2,
        sector_3_seconds=s3,
        compound=compound_str,
        is_valid=is_valid,
        start_time=start_time,
        source="fastf1",
    )


def normalize_fastf1_telemetry(
    tel_df: pd.DataFrame,
    driver_code: str,
    driver_number: Optional[int] = None,
    lap_number: Optional[int] = None,
) -> List[NormalizedTelemetryPoint]:
    """Normalize raw FastF1 telemetry DataFrame into canonical list of NormalizedTelemetryPoint.

    IMPORTANT:
    - Multi-rate data preserved.
    - No resampling or interpolation is applied.
    - Missing channels explicitly set to None.
    - Original timestamps and raw observations preserved.
    """
    if tel_df is None or tel_df.empty:
        return []

    points: List[NormalizedTelemetryPoint] = []

    has_date = "Date" in tel_df.columns
    has_time = "Time" in tel_df.columns
    has_dist = "Distance" in tel_df.columns
    has_x = "X" in tel_df.columns
    has_y = "Y" in tel_df.columns
    has_z = "Z" in tel_df.columns
    has_speed = "Speed" in tel_df.columns
    has_throttle = "Throttle" in tel_df.columns
    has_brake = "Brake" in tel_df.columns
    has_gear = "nGear" in tel_df.columns
    has_rpm = "RPM" in tel_df.columns
    has_drs = "DRS" in tel_df.columns

    for _, row in tel_df.iterrows():
        # Timestamp extraction
        ts = None
        if has_date:
            raw_date = row["Date"]
            if raw_date is not None and not pd.isna(raw_date):
                if isinstance(raw_date, pd.Timestamp):
                    ts = raw_date.to_pydatetime()
                elif isinstance(raw_date, datetime):
                    ts = raw_date

        # Time offset
        time_offset = 0.0
        if has_time:
            raw_time = row["Time"]
            if raw_time is not None and not pd.isna(raw_time):
                if isinstance(raw_time, (timedelta, pd.Timedelta)):
                    time_offset = round(raw_time.total_seconds(), 4)
                else:
                    try:
                        time_offset = round(float(raw_time), 4)
                    except (ValueError, TypeError):
                        pass

        # Distance
        dist = None
        if has_dist:
            raw_dist = row["Distance"]
            if raw_dist is not None and not pd.isna(raw_dist):
                dist = round(float(raw_dist), 2)

        # Spatial X, Y, Z (FastF1 coordinates are in decimeters; convert to SI meters: / 10.0)
        x = round(float(row["X"]) / 10.0, 3) if has_x and not pd.isna(row["X"]) else None
        y = round(float(row["Y"]) / 10.0, 3) if has_y and not pd.isna(row["Y"]) else None
        z = round(float(row["Z"]) / 10.0, 3) if has_z and not pd.isna(row["Z"]) else None

        # Speed
        speed = float(row["Speed"]) if has_speed and not pd.isna(row["Speed"]) else None

        # Throttle
        throttle = float(row["Throttle"]) if has_throttle and not pd.isna(row["Throttle"]) else None

        # Brake (FastF1 can be boolean or float)
        brake = None
        if has_brake:
            raw_brake = row["Brake"]
            if not pd.isna(raw_brake):
                if isinstance(raw_brake, bool):
                    brake = 100.0 if raw_brake else 0.0
                else:
                    try:
                        val = float(raw_brake)
                        brake = 100.0 if val > 0 and val <= 1.0 else val
                    except (ValueError, TypeError):
                        pass

        # Gear
        gear = int(row["nGear"]) if has_gear and not pd.isna(row["nGear"]) else None

        # RPM
        rpm = int(row["RPM"]) if has_rpm and not pd.isna(row["RPM"]) else None

        # DRS
        drs = int(row["DRS"]) if has_drs and not pd.isna(row["DRS"]) else None

        points.append(
            NormalizedTelemetryPoint(
                timestamp=ts,
                time_offset=time_offset,
                driver_code=driver_code,
                driver_number=driver_number,
                lap_number=lap_number,
                distance=dist,
                x=x,
                y=y,
                z=z,
                speed=speed,
                throttle=throttle,
                brake=brake,
                steering=None,  # Not present in FastF1 telemetry feeds
                gear=gear,
                rpm=rpm,
                drs=drs,
                accel_x=None,
                accel_y=None,
                source="fastf1",
            )
        )

    return points
