"""Unit tests for FastF1 data normalizer."""

from datetime import datetime, date, timedelta
import pandas as pd
import pytest

from app.data.fastf1.normalizer import (
    slugify,
    normalize_fastf1_event,
    normalize_fastf1_session,
    normalize_fastf1_driver,
    normalize_fastf1_lap,
    normalize_fastf1_telemetry,
)


def test_slugify():
    assert slugify("Italian Grand Prix") == "italian-grand-prix"
    assert slugify("São Paulo Grand Prix!") == "sao-paulo-grand-prix"
    assert slugify("  Practice 1  ") == "practice-1"


def test_normalize_fastf1_event():
    event_data = pd.Series({
        "RoundNumber": 16,
        "Country": "Italy",
        "Location": "Monza",
        "OfficialEventName": "FORMULA 1 PIRELLI GRAN PREMIO D'ITALIA 2024",
        "EventDate": pd.Timestamp("2024-09-01"),
        "EventName": "Italian Grand Prix",
        "EventFormat": "conventional",
        "F1ApiSupport": True,
    })

    norm = normalize_fastf1_event(event_data, season=2024)
    assert norm.id == "f1-2024-italian-grand-prix"
    assert norm.series == "Formula 1"
    assert norm.season == "2024"
    assert norm.round_number == 16
    assert norm.name == "Italian Grand Prix"
    assert norm.circuit_name == "Autodromo Nazionale Monza"
    assert norm.country == "Italy"
    assert norm.city == "Monza"
    assert norm.event_date == date(2024, 9, 1)
    assert norm.source == "fastf1"


def test_normalize_fastf1_driver():
    driver_row = pd.Series({
        "DriverNumber": "16",
        "BroadcastName": "C LECLERC",
        "FullName": "Charles Leclerc",
        "Abbreviation": "LEC",
        "DriverId": "leclerc",
        "TeamName": "Ferrari",
        "TeamColor": "E80020",
        "FirstName": "Charles",
        "LastName": "Leclerc",
        "CountryCode": "MON",
    })

    norm = normalize_fastf1_driver(driver_row, session_id="f1-2024-monza-race")
    assert norm.code == "LEC"
    assert norm.number == 16
    assert norm.full_name == "Charles Leclerc"
    assert norm.team == "Ferrari"
    assert norm.team_color == "#E80020"
    assert norm.nationality == "MON"
    assert norm.source == "fastf1"


def test_normalize_fastf1_lap():
    lap_row = pd.Series({
        "LapNumber": 12,
        "LapTime": pd.Timedelta(seconds=81.456),
        "Sector1Time": pd.Timedelta(seconds=27.123),
        "Sector2Time": pd.Timedelta(seconds=26.456),
        "Sector3Time": pd.Timedelta(seconds=27.877),
        "Compound": "HARD",
        "Deleted": False,
        "IsAccurate": True,
        "LapStartDate": pd.Timestamp("2024-09-01 13:42:10"),
    })

    norm = normalize_fastf1_lap(lap_row, driver_code="LEC", driver_number=16)
    assert norm.driver_code == "LEC"
    assert norm.driver_number == 16
    assert norm.lap_number == 12
    assert norm.lap_time_seconds == 81.456
    assert norm.sector_1_seconds == 27.123
    assert norm.compound == "HARD"
    assert norm.is_valid is True


def test_normalize_fastf1_telemetry():
    tel_df = pd.DataFrame([
        {
            "Date": pd.Timestamp("2024-09-01 13:42:10.100"),
            "Time": pd.Timedelta(seconds=10.1),
            "Distance": 150.5,
            "X": 1024.5,
            "Y": -512.3,
            "Z": 12.0,
            "Speed": 315.4,
            "Throttle": 100.0,
            "Brake": 0.0,
            "nGear": 7,
            "RPM": 11800,
            "DRS": 12,
        },
        {
            "Date": pd.Timestamp("2024-09-01 13:42:10.200"),
            "Time": pd.Timedelta(seconds=10.2),
            "Distance": 158.8,
            "X": 1030.1,
            "Y": -508.2,
            "Z": 12.1,
            "Speed": 318.0,
            "Throttle": 100.0,
            "Brake": False,
            "nGear": 8,
            "RPM": 11950,
            "DRS": 12,
        },
    ])

    points = normalize_fastf1_telemetry(tel_df, driver_code="VER", driver_number=1, lap_number=15)
    assert len(points) == 2
    assert points[0].driver_code == "VER"
    assert points[0].speed == 315.4
    assert points[0].x == 102.45
    assert points[0].gear == 7
    assert points[0].steering is None  # Unavailable channel is None
    assert points[1].brake == 0.0  # Boolean False converted to 0.0
