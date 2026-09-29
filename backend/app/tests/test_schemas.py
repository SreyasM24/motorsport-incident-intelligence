"""Unit tests for Pydantic v2 schemas and validation constraints."""

import pytest
from pydantic import ValidationError
from app.schemas.telemetry import TelemetryPointSchema, TelemetryQueryParams
from app.schemas.assistant import AssistantQueryRequest
from app.schemas.race import RaceResponse
from app.schemas.incident import IncidentSummary, IncidentStatusUpdate


def test_telemetry_point_valid():
    """Verify valid telemetry frame parses correctly."""
    point = TelemetryPointSchema(
        time_offset=0.04,
        timestamp="13:42:18.4",
        speed_a=320.5,
        throttle_a=98.0,
        brake_a=0.0,
        steer_a=-2.5,
        gear_a=8,
        accel_a=-0.2,
        speed_b=318.0,
        throttle_b=100.0,
        brake_b=0.0,
        steer_b=0.0,
        gear_b=8,
        accel_b=-0.1,
        gap_meters=2.45,
        closing_speed_ms=4.12,
        lateral_dist_meters=2.10,
    )
    assert point.speed_a == 320.5
    assert point.gap_meters == 2.45
    # Verify camelCase serialization for frontend
    dump = point.model_dump(by_alias=True)
    assert "timeOffset" in dump
    assert "speedA" in dump
    assert "gapMeters" in dump


def test_telemetry_point_invalid_throttle():
    """Verify throttle values over 100% fail validation."""
    with pytest.raises(ValidationError):
        TelemetryPointSchema(
            time_offset=0.0,
            timestamp="13:42:18.4",
            speed_a=300.0,
            throttle_a=150.0,  # Invalid: > 100%
            brake_a=0.0,
            steer_a=0.0,
            speed_b=300.0,
            throttle_b=100.0,
            brake_b=0.0,
            steer_b=0.0,
            gap_meters=5.0,
            closing_speed_ms=0.0,
            lateral_dist_meters=3.0,
        )


def test_telemetry_query_params_safety_limit():
    """Verify query limit is bounded by max=2000 to prevent unbounded dumps."""
    with pytest.raises(ValidationError):
        TelemetryQueryParams(driver_a="VER", limit=50000)  # Exceeds max 2000


def test_assistant_query_request_validation():
    """Verify empty query string fails validation."""
    with pytest.raises(ValidationError):
        AssistantQueryRequest(query="")


def test_race_response_camel_case():
    """Verify race schema serializes into expected camelCase attributes."""
    race = RaceResponse(
        id="ita-2024",
        name="Italian Grand Prix",
        circuit="Monza",
        country="Italy",
        season="2024",
        round=16,
        year=2024,
        date="2024-09-01",
    )
    dump = race.model_dump(by_alias=True)
    assert dump["id"] == "ita-2024"
    assert "sessionType" in dump
    assert "driversCount" in dump
    assert "regulationSet" in dump
