"""Pydantic schemas for Sessions and Session Overview metrics."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SessionResponse(BaseModel):
    """Core session model representation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str
    race_id: str
    session_type: str
    name: str
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_laps: Optional[int] = None
    status: str = "ANALYSIS_READY"


class SessionSummaryResponse(BaseModel):
    """Aggregate dashboard metrics and status flags for a session."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: str
    race_name: str
    circuit: str
    drivers_count: int = Field(default=20, description="Drivers active in session")
    candidates_count: int = Field(default=0, description="Total algorithmic interaction candidates")
    requires_review_count: int = Field(default=0, description="Candidates needing human steward review")
    reviewed_count: int = Field(default=0, description="Incidents reviewed by stewards")

    # Ingest / Processing Status Flags
    telemetry_status: str = Field(default="CONNECTED", description="CAN-bus and GPS ingest health")
    incident_analysis_status: str = Field(default="AVAILABLE", description="Reconstruction engine status")
    regulations_status: str = Field(default="CONNECTED", description="FIA statutory knowledge index status")
    video_status: str = Field(default="AVAILABLE", description="Video sync status")
    ai_analysis_status: str = Field(default="AVAILABLE", description="AI Steward Assistant status")


class RaceActivityPoint(BaseModel):
    """Lap-by-lap incident candidate density for Recharts visualization."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    lap: int = Field(..., ge=1, description="Lap number")
    candidates: int = Field(default=0, ge=0, description="Total interactions flagged")
    abnormal: int = Field(default=0, ge=0, description="Interaction anomalies detected")
    high_confidence: int = Field(default=0, ge=0, description="High-correlation interaction candidates")
