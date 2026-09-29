"""Pydantic schemas for Races and Grand Prix events."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class RaceSessionSchema(BaseModel):
    """Sub-session summary within a race weekend."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    name: str = Field(..., description="Session name, e.g. Practice 1, Qualifying, Race")
    laps: Optional[int] = Field(default=None, description="Number of laps completed or scheduled")
    status: str = Field(default="ANALYSIS READY", description="Session analysis ingest status")


class RaceResponse(BaseModel):
    """Complete race event schema formatted for frontend consumers."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str = Field(..., description="Unique event identifier, e.g. ita-2024")
    name: str = Field(..., description="Official Grand Prix name")
    circuit: str = Field(..., description="Circuit name")
    country: str = Field(..., description="Host country")
    season: str = Field(..., description="Championship season year as string, e.g. 2024")
    round: Optional[int] = Field(default=None, description="Championship round number")
    year: int = Field(..., description="Championship year as integer")
    session_type: str = Field(default="Race", description="Primary focus session type")
    date: str = Field(..., description="Event date string (YYYY-MM-DD)")
    drivers_count: int = Field(default=20, description="Number of drivers entered")
    candidates_count: int = Field(default=0, description="Total incident candidates flagged")
    confirmed_count: int = Field(default=0, description="Total incidents reviewed by stewards")
    review_count: int = Field(default=0, description="Active incidents currently requiring review")
    status: str = Field(default="ANALYSIS READY", description="Event analysis status")
    telemetry_available: bool = Field(default=True, description="True if telemetry stream is accessible")
    video_available: bool = Field(default=False, description="True if synchronized video feeds are linked")
    regulation_set: str = Field(default="FIA Sporting Regulations 2024", description="Applicable regulatory document")
    sessions: List[RaceSessionSchema] = Field(default_factory=list, description="List of sessions in this Grand Prix")


class RaceListResponse(BaseModel):
    """List response wrapper for championship races."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: List[RaceResponse]
    total: int
