"""Normalized internal motorsport domain models.

Isolates the rest of the application from raw FastF1 DataFrames or OpenF1 JSON payloads.
These domain models represent pure canonical representations of motorsport entities.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Any


@dataclass
class NormalizedRace:
    """Canonical representation of a Grand Prix / championship event."""
    id: str
    series: str = "Formula 1"
    season: str = "2024"
    round_number: Optional[int] = None
    name: str = ""
    official_name: Optional[str] = None
    circuit_name: str = ""
    country: str = ""
    city: Optional[str] = None
    event_date: Optional[date] = None
    source: str = "fastf1"
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedSession:
    """Canonical representation of a track session within an event."""
    id: str
    race_id: str
    session_type: str  # "Practice 1", "Practice 2", "Practice 3", "Qualifying", "Sprint", "Race"
    session_name: str
    session_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_laps: Optional[int] = None
    status: str = "ANALYSIS_READY"
    source: str = "fastf1"
    source_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedDriver:
    """Canonical representation of a driver in a session."""
    id: str
    session_id: str
    code: str  # 3-letter abbreviation, e.g. "VER"
    number: int
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    abbreviation: str = ""
    team: str = "Unknown Team"
    team_color: Optional[str] = None
    secondary_color: Optional[str] = None
    nationality: Optional[str] = None
    laps_completed: int = 0
    avg_speed_kmh: Optional[float] = None
    max_speed_kmh: Optional[float] = None
    source: str = "fastf1"
    source_id: Optional[str] = None

    def __post_init__(self):
        if not self.abbreviation:
            self.abbreviation = self.code


@dataclass
class NormalizedLap:
    """Canonical representation of a driver's lap in a session."""
    driver_code: str
    driver_number: int
    lap_number: int
    lap_time_seconds: Optional[float] = None
    sector_1_seconds: Optional[float] = None
    sector_2_seconds: Optional[float] = None
    sector_3_seconds: Optional[float] = None
    compound: Optional[str] = None
    is_valid: bool = True
    start_time: Optional[datetime] = None
    source: str = "fastf1"


@dataclass
class NormalizedTelemetryPoint:
    """Canonical multi-channel telemetry frame for a single driver.

    Note: FastF1 telemetry is multi-rate; channels may be None when not
    measured or available from the source feed.
    """
    timestamp: Optional[datetime] = None
    time_offset: float = 0.0
    driver_code: str = ""
    driver_number: Optional[int] = None
    lap_number: Optional[int] = None
    distance: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    speed: Optional[float] = None
    throttle: Optional[float] = None
    brake: Optional[float] = None
    steering: Optional[float] = None
    gear: Optional[int] = None
    rpm: Optional[int] = None
    drs: Optional[int] = None
    accel_x: Optional[float] = None
    accel_y: Optional[float] = None
    source: str = "fastf1"


@dataclass
class NormalizedRaceControlMessage:
    """Canonical race control / flag status message from steward feed."""
    timestamp: Optional[datetime] = None
    lap_number: Optional[int] = None
    category: Optional[str] = None
    message: str = ""
    flag: Optional[str] = None
    scope: Optional[str] = None
    sector: Optional[int] = None
    source: str = "openf1"
