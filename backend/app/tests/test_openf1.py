"""Unit tests for OpenF1 client, normalizer, and error handling using mocked responses."""

from unittest.mock import MagicMock, patch
import pytest
import httpx

from app.data.openf1.client import OpenF1Client
from app.data.openf1.normalizer import (
    normalize_openf1_session,
    normalize_openf1_driver,
    normalize_openf1_lap,
    normalize_openf1_car_data,
    normalize_openf1_race_control,
)
from app.data.openf1.exceptions import OpenF1Error, OpenF1RateLimitError, OpenF1TimeoutError


def test_normalize_openf1_session():
    sample_raw = {
        "session_key": 9568,
        "session_name": "Race",
        "date_start": "2024-09-01T13:00:00+00:00",
        "date_end": "2024-09-01T15:00:00+00:00",
        "year": 2024,
        "circuit_key": 39,
        "circuit_short_name": "Monza",
        "country_name": "Italy",
        "location": "Monza",
        "session_type": "Race",
    }
    norm = normalize_openf1_session(sample_raw)
    assert norm.id == "f1-2024-italy-race"
    assert norm.session_type == "Race"
    assert norm.source == "openf1"
    assert norm.source_id == "9568"
    assert norm.start_time is not None


def test_normalize_openf1_driver():
    sample_raw = {
        "broadcast_name": "C LECLERC",
        "country_code": "MON",
        "driver_number": 16,
        "first_name": "Charles",
        "full_name": "Charles Leclerc",
        "last_name": "Leclerc",
        "name_acronym": "LEC",
        "session_key": 9568,
        "team_colour": "E80020",
        "team_name": "Ferrari",
    }
    norm = normalize_openf1_driver(sample_raw, session_id="f1-2024-italy-race")
    assert norm.code == "LEC"
    assert norm.number == 16
    assert norm.team == "Ferrari"
    assert norm.team_color == "#E80020"
    assert norm.source == "openf1"


def test_normalize_openf1_car_data():
    car_points = [
        {
            "brake": 0,
            "date": "2024-09-01T13:42:10.100Z",
            "driver_number": 16,
            "drs": 12,
            "n_gear": 7,
            "rpm": 11500,
            "session_key": 9568,
            "speed": 320,
            "throttle": 100,
        }
    ]
    loc_points = [
        {
            "date": "2024-09-01T13:42:10.100Z",
            "driver_number": 16,
            "session_key": 9568,
            "x": 1024.5,
            "y": -512.3,
            "z": 12.0,
        }
    ]

    points = normalize_openf1_car_data(car_points, location_points=loc_points, driver_code="LEC")
    assert len(points) == 1
    assert points[0].driver_code == "LEC"
    assert points[0].speed == 320.0
    assert points[0].x == 102.45
    assert points[0].steering is None  # Unavailable in OpenF1
    assert points[0].source == "openf1"


def test_normalize_openf1_race_control():
    sample_raw = {
        "category": "Flag",
        "date": "2024-09-01T13:45:20+00:00",
        "driver_number": None,
        "flag": "YELLOW",
        "lap_number": 14,
        "message": "YELLOW FLAG IN SECTOR 2",
        "scope": "Sector",
        "sector": 2,
        "session_key": 9568,
    }
    norm = normalize_openf1_race_control(sample_raw)
    assert norm.category == "Flag"
    assert norm.flag == "YELLOW"
    assert norm.sector == 2
    assert norm.lap_number == 14


def test_openf1_client_retries_on_rate_limit():
    client = OpenF1Client(base_url="https://mock.openf1.org/v1", max_retries=2)

    # Mock response: first 429, then 200
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.headers = {"Retry-After": "0"}

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = [{"session_key": 1234}]

    with patch.object(client, "_get_client") as mock_get_client:
        mock_http = MagicMock()
        mock_http.get.side_effect = [mock_resp_429, mock_resp_200]
        mock_get_client.return_value = mock_http

        result = client.get_sessions(year=2024)
        assert len(result) == 1
        assert result[0]["session_key"] == 1234
        assert mock_http.get.call_count == 2
