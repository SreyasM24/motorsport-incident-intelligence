"""Base motorsport data source abstraction and protocol."""

from abc import ABC, abstractmethod
from typing import List, Optional, Union
from app.data.domain import (
    NormalizedRace,
    NormalizedSession,
    NormalizedDriver,
    NormalizedLap,
    NormalizedTelemetryPoint,
)


class BaseDataSource(ABC):
    """Abstract interface defining the contract for motorsport data providers (FastF1, OpenF1)."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source provider (e.g. 'fastf1', 'openf1')."""
        pass

    @abstractmethod
    def get_season_events(self, season: int) -> List[NormalizedRace]:
        """Retrieve all Grand Prix events for a given championship season."""
        pass

    @abstractmethod
    def get_event(self, season: int, round_or_name: Union[int, str]) -> NormalizedRace:
        """Retrieve a specific championship event by round number or race name."""
        pass

    @abstractmethod
    def get_session(
        self, season: int, round_or_name: Union[int, str], session_identifier: str
    ) -> NormalizedSession:
        """Retrieve metadata for a specific session within an event."""
        pass

    @abstractmethod
    def get_session_drivers(
        self, season: int, round_or_name: Union[int, str], session_identifier: str
    ) -> List[NormalizedDriver]:
        """Retrieve the roster of drivers participating in a session."""
        pass

    @abstractmethod
    def get_session_laps(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        driver: Optional[str] = None,
    ) -> List[NormalizedLap]:
        """Retrieve lap timing records for a session, optionally filtered by driver."""
        pass

    @abstractmethod
    def get_driver_telemetry(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        driver: str,
        lap: Optional[int] = None,
    ) -> List[NormalizedTelemetryPoint]:
        """Retrieve raw telemetry data points for a specific driver and optional lap."""
        pass
