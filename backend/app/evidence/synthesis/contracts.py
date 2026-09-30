"""Canonical data contracts for the Unified Steward Evidence Dossier & Synthesis Layer.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS (PROMPT 16):
    1. Zero Autonomous Guilt or Fault: The dossier is NOT a verdict. It answers:
       "What evidence is available, how reliable is each stream, where do they agree,
       where do they disagree, and what remains unavailable for human steward review?"
    2. Zero Composite AI Scores: No "incident confidence score", "guilt score",
       "fault score", "violation probability", or "composite AI score".
    3. Explicit Evidence Semantics: Strictly distinguishes OBSERVED, DERIVED,
       MODEL_DERIVED, DOCUMENTARY, and UNAVAILABLE. Never upgrades MODEL_DERIVED to OBSERVED.
    4. Lineage & Double-Counting Prevention: Explicitly tracks evidence lineage to prevent
       treating correlated or derived features as independent observations.
    5. Discrepancy Severity: Severity (LOW, MEDIUM, HIGH, UNRESOLVED) reflects empirical/technical
       alignment discrepancies, NEVER driver fault or sporting guilt.
    6. Descriptive Regulation Linkage: Regulations are linked descriptively. No automated
       FIA violation verdicts are issued.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


# ==============================================================================
# 1. ENUMS & EVIDENCE TAXONOMY
# ==============================================================================

class EvidenceType(str, Enum):
    """Categorization of evidence streams."""
    TELEMETRY = "TELEMETRY"
    REFERENCE_BASELINE = "REFERENCE_BASELINE"
    OVERTAKE_GEOMETRY = "OVERTAKE_GEOMETRY"
    ML_INTERACTION = "ML_INTERACTION"
    VIDEO_SYNCHRONIZATION = "VIDEO_SYNCHRONIZATION"
    VISUAL = "VISUAL"
    COMPUTER_VISION = "COMPUTER_VISION"
    REGULATION = "REGULATION"


class EvidenceStatus(str, Enum):
    """Rigorous epistemic classification of evidence items."""
    OBSERVED = "OBSERVED"              # Direct physical/sensor measurement (speed, throttle, brake, raw video)
    DERIVED = "DERIVED"                # Deterministic mathematical transformation (closing rate, trajectory delta, overlap %)
    MODEL_DERIVED = "MODEL_DERIVED"    # Hypothesis emitted by statistical or ML/CV model (CV track, ML anomaly probability)
    DOCUMENTARY = "DOCUMENTARY"        # Official regulatory or race control documentary reference
    UNAVAILABLE = "UNAVAILABLE"        # Unlinked, unobserved, or commercially restricted stream


class ConsistencyStatus(str, Enum):
    """Cross-modal consistency rating between two or more evidence streams."""
    CONSISTENT = "CONSISTENT"
    PARTIALLY_CONSISTENT = "PARTIALLY_CONSISTENT"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class DiscrepancySeverity(str, Enum):
    """Technical/alignment discrepancy magnitude. NOT a fault or guilt measure."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNRESOLVED = "UNRESOLVED"


# ==============================================================================
# 2. CANONICAL EVIDENCE ITEM & LINEAGE CONTRACTS
# ==============================================================================

class EvidenceItem(BaseModel):
    """A single inspectable evidence observation or derivation with explicit lineage."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evidence_id: str
    evidence_type: EvidenceType
    source_layer: str
    status: EvidenceStatus
    observation: str
    value: Optional[Any] = None
    unit: Optional[str] = None
    timestamp: Optional[str] = None
    event_relative_time_sec: Optional[float] = None
    confidence_or_quality: Optional[str] = None
    measurement_basis: str = Field(
        default="EMPIRICAL_SENSOR",
        description="e.g. SENSOR_ECU_CAN, 2D_CARTESIAN_RESAMPLED, BOUNDED_2D_PROJECTION, REGULATION_TEXT",
    )
    provenance: str
    limitations: List[str] = Field(default_factory=list)
    analysis_version: str = "1.0"
    parent_evidence_ids: List[str] = Field(
        default_factory=list,
        description="IDs of raw/upstream evidence items from which this item was derived (for lineage tracking)",
    )


class EvidenceQualityRecord(BaseModel):
    """Quality and availability assessment for an individual evidence stream."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    stream_name: str
    evidence_type: EvidenceType
    status: EvidenceStatus
    availability: str = Field(..., description="AVAILABLE, PARTIAL, UNAVAILABLE")
    temporal_validity: str = "VALID"
    spatial_validity: str = "VALID"
    provenance_source: str
    measurement_uncertainty: Optional[str] = None
    missingness_notes: Optional[str] = None
    model_dependency: Optional[str] = None
    evaluation_status: str = "NOT_APPLICABLE"


# ==============================================================================
# 3. DISCREPANCY & CONSISTENCY CONTRACTS
# ==============================================================================

class CrossModalDiscrepancy(BaseModel):
    """A detected divergence, tension, or alignment issue between two evidence streams."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    discrepancy_id: str
    evidence_stream_a: str
    evidence_stream_b: str
    metric: str
    observed_difference: str
    expected_tolerance: str
    severity: DiscrepancySeverity
    status: str = "OPEN"
    explanation: str
    provenance: str
    affected_evidence_ids: List[str] = Field(default_factory=list)


class EvidenceConsensus(BaseModel):
    """Multi-modal consensus analysis WITHOUT a weighted single AI score."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    supporting_evidence_streams: List[str] = Field(default_factory=list)
    conflicting_evidence_streams: List[str] = Field(default_factory=list)
    unavailable_evidence_streams: List[str] = Field(default_factory=list)
    independent_observation_count: int = Field(
        ...,
        description="Number of distinct root evidence origins, preventing double-counting of derived features",
    )
    total_evidence_items: int = 0
    consensus_summary: str
    steward_inspection_guidance: str


# ==============================================================================
# 4. NORMALIZED TIMELINE & REGULATION LINKAGE CONTRACTS
# ==============================================================================

class NormalizedTimelineEvent(BaseModel):
    """A chronologically ordered milestone event in the normalized incident window."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    timestamp: str
    event_relative_time_sec: float
    source: str
    description: str
    evidence_status: EvidenceStatus
    provenance: str
    evidence_ref: Optional[str] = None


class DescriptiveRegulationLink(BaseModel):
    """Descriptive reference linking observed evidence to statutory FIA sporting code."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    regulation_id: str
    document: str
    article: str
    title: str
    source: str
    evidence_relationship: str = Field(
        ...,
        description="Descriptive explanation of relevance. NEVER asserts a violation or penalty.",
    )
    relevant_evidence_ids: List[str] = Field(default_factory=list)
    provenance: str


# ==============================================================================
# 5. CANONICAL STEWARD EVIDENCE DOSSIER
# ==============================================================================

class StewardEvidenceDossier(BaseModel):
    """The master discrepancy-aware Steward Evidence Dossier for human steward panel inspection."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    dossier_id: str
    candidate_id: str
    incident_id: Optional[str] = None
    session_id: str
    event_type: str
    lap_number: int
    turn: str
    generated_at: str
    dossier_version: str = "2.0"
    analysis_version: str = "PROMPT_16_SYNTHESIS"

    # Participants
    driver_a: str
    driver_b: str
    car_number_a: Optional[str] = None
    car_number_b: Optional[str] = None
    team_a: Optional[str] = None
    team_b: Optional[str] = None

    # Human Review State (Strictly human controlled; never auto-decided)
    review_status: str = "REQUIRES_REVIEW"
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None

    # Unified Chronological Timeline
    timeline: List[NormalizedTimelineEvent] = Field(default_factory=list)

    # Granular Evidence Items (Individually Inspectable)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)

    # Stream Quality Assessments
    stream_quality: List[EvidenceQualityRecord] = Field(default_factory=list)

    # Cross-Modal Consistency & Consensus (No single composite AI score)
    cross_modal_consistency: ConsistencyStatus
    consensus: EvidenceConsensus
    discrepancies: List[CrossModalDiscrepancy] = Field(default_factory=list)

    # Descriptive Regulations
    regulations: List[DescriptiveRegulationLink] = Field(default_factory=list)

    # Historical Comparable Evidence (Prompt 23 Explainable Retrieval)
    historical_comparable_evidence: Optional[Any] = None

    # General Limitations & Provenance
    limitations: List[str] = Field(default_factory=list)
    provenance_summary: str
    steward_doctrine: str = (
        "CRITICAL STEWARD DOCTRINE: This dossier provides empirical evidence synthesis and discrepancy "
        "analysis for human motorsport stewards. It strictly does NOT decide driver guilt, apportion fault, "
        "issue penalties, or declare regulatory violations. Human stewards retain exclusive adjudicative authority."
    )


class DossierExportPayload(BaseModel):
    """Deterministic, machine-readable export wrapper for external FIA audit integration."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    export_type: str = "JSON_STEWARD_DOSSIER"
    schema_version: str = "2.0"
    exported_at: str
    dossier: StewardEvidenceDossier


__all__ = [
    "ConsistencyStatus",
    "CrossModalDiscrepancy",
    "DescriptiveRegulationLink",
    "DiscrepancySeverity",
    "DossierExportPayload",
    "EvidenceConsensus",
    "EvidenceItem",
    "EvidenceQualityRecord",
    "EvidenceStatus",
    "EvidenceType",
    "NormalizedTimelineEvent",
    "StewardEvidenceDossier",
]
