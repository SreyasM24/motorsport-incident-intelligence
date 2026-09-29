"""Pydantic schemas for the AI Steward Assistant interface."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AssistantQueryRequest(BaseModel):
    """Conversational question sent by steward or user."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    query: str = Field(..., min_length=2, max_length=1000, description="User inquiry text")
    incident_id: Optional[str] = Field(default=None, description="Active incident ID context, e.g. INC-024")
    session_id: Optional[str] = Field(default=None, description="Active session ID context, e.g. ita-2024-race")


class EvidenceChip(BaseModel):
    """Badge highlighting specific evidence source consulted by assistant."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    label: str
    type: str = Field(default="telemetry", description="telemetry, timeline, regulation, or response")
    target_id: Optional[str] = None


class EvidenceLink(BaseModel):
    """Deep-link navigating steward directly to specific evidence module."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    label: str
    target_view: str
    incident_id: Optional[str] = None


class AssistantMessageSchema(BaseModel):
    """Single conversational turn returned by AI Steward Assistant."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    sender: str = Field(default="assistant", description="user or assistant")
    timestamp: str
    text: str
    evidence_chips: List[EvidenceChip] = Field(default_factory=list)
    evidence_links: List[EvidenceLink] = Field(default_factory=list)
    suggested_follow_ups: List[str] = Field(default_factory=list)
