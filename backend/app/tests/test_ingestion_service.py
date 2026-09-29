"""Unit tests for IngestionService using mocked data sources."""

from unittest.mock import MagicMock
import pytest
from app.services.ingestion_service import IngestionService
from app.data.domain import (
    NormalizedRace,
    NormalizedSession,
    NormalizedDriver,
    NormalizedTelemetryPoint,
)


@pytest.fixture
def mock_fastf1_source():
    source = MagicMock()
    source.source_name = "fastf1"

    sample_race = NormalizedRace(
        id="f1-2024-monza",
        name="Italian Grand Prix",
        circuit_name="Autodromo Nazionale Monza",
        country="Italy",
        round_number=16,
        season="2024",
    )
    source.get_season_events.return_value = [sample_race]
    source.get_event.return_value = sample_race

    sample_session = NormalizedSession(
        id="f1-2024-monza-race",
        race_id="f1-2024-monza",
        session_type="Race",
        session_name="Italian Grand Prix Race",
        total_laps=53,
    )
    source.get_session.return_value = sample_session

    sample_driver = NormalizedDriver(
        id="f1-2024-monza-race-ver",
        session_id="f1-2024-monza-race",
        code="VER",
        number=1,
        full_name="Max Verstappen",
        team="Red Bull Racing",
        team_color="#3671C6",
    )
    source.get_session_drivers.return_value = [sample_driver]

    sample_pt = NormalizedTelemetryPoint(
        driver_code="VER",
        driver_number=1,
        lap_number=1,
        speed=310.0,
        throttle=100.0,
        brake=0.0,
        gear=7,
        rpm=11600,
        source="fastf1",
    )
    source.get_driver_telemetry.return_value = [sample_pt]

    return source


def test_ingestion_service_calendar(mock_fastf1_source):
    service = IngestionService(fastf1_source=mock_fastf1_source)
    races = service.load_season_calendar(2024)
    assert len(races) == 1
    assert races[0].name == "Italian Grand Prix"
    assert races[0].round_number == 16
    mock_fastf1_source.get_season_events.assert_called_once_with(2024)


def test_ingestion_service_session_metadata(mock_fastf1_source):
    service = IngestionService(fastf1_source=mock_fastf1_source)
    session = service.load_session_metadata(2024, "Monza", "Race")
    assert session.session_type == "Race"
    assert session.total_laps == 53
    mock_fastf1_source.get_session.assert_called_once_with(2024, "Monza", "Race")


def test_ingestion_service_driver_telemetry(mock_fastf1_source):
    service = IngestionService(fastf1_source=mock_fastf1_source)
    points = service.load_driver_telemetry(2024, "Monza", "Race", driver="VER", lap=1)
    assert len(points) == 1
    assert points[0].driver_code == "VER"
    assert points[0].speed == 310.0
    mock_fastf1_source.get_driver_telemetry.assert_called_once_with(
        season=2024, round_or_name="Monza", session_identifier="Race", driver="VER", lap=1
    )
