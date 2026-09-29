"""Pydantic schemas for FIA Regulations and evidence-rule linkages."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class RegulationSchema(BaseModel):
    """Normalized regulation record from the statutory repository."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str
    series: str = "Formula 1"
    season: str = "2024"
    document: str
    document_version: Optional[str] = None
    article: str
    title: str
    text: str
    source_url: Optional[str] = None
    source: str = "FIA World Motor Sport Council"


class RelevantRegulationSchema(BaseModel):
    """Incident-contextual regulation match for evidence presentation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    document: str
    article: str
    title: str
    regulation_text_placeholder: str
    why_relevant: str
    match_reason: str
    relevance: str = Field(default="High", description="High, Medium, or Low")
    source: str
    source_url: Optional[str] = None


class EvidenceRegulationConnectionSchema(BaseModel):
    """3-way evidentiary link: Observed Evidence -> Relevant Regulation -> Steward Review Action."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    observed_evidence: str
    relevant_regulation: str
    steward_review_action: str


class RegulationListResponse(BaseModel):
    """Collection wrapper for regulation repository search results."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: List[RegulationSchema]
    total: int
