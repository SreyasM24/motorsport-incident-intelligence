"""Pydantic schemas for Drivers and driver session telemetry statistics."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DriverStats(BaseModel):
    """Aggregate session telemetry statistics for driver modal."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    laps_completed: int = Field(default=0, ge=0, description="Total completed laps")
    avg_speed_kmh: float = Field(default=0.0, ge=0.0, description="Average lap speed in km/h")
    max_speed_kmh: float = Field(default=0.0, ge=0.0, description="Peak trap speed in km/h")
    incidents_involved: int = Field(default=0, ge=0, description="Flagged interactions where driver participated")
    interactions_detected: int = Field(default=0, ge=0, description="Total close tracking instances")


class DriverResponse(BaseModel):
    """Driver profile and livery representation for frontend presentation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    code: str = Field(..., description="3-letter official driver code, e.g. VER, HAM")
    number: int = Field(..., description="Driver permanent competition number")
    name: str = Field(..., description="Full driver name")
    team: str = Field(..., description="Constructor team name")
    team_color: str = Field(default="#E10600", description="Primary livery hex color code")
    secondary_color: Optional[str] = Field(default=None, description="Secondary livery hex color code")
    country: str = Field(..., description="3-letter nationality code, e.g. NED, GBR")
    stats: DriverStats = Field(default_factory=DriverStats, description="Performance statistics")
