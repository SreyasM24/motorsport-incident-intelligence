"""Canonical data models for citation-grounded evidence retrieval (Prompt 21).

CRITICAL JURISPRUDENTIAL & EPISTEMIC GUARDRAILS:
    1. Zero Autonomous Adjudication: Answers "What documentary evidence is relevant?",
       NEVER "Who is guilty?", "Who caused the incident?", or "What penalty should be given?".
    2. No Orphaned Text: Every chunk must trace to document_id, source_url, article/section,
       and document_version.
    3. Provenance & Licensing: Full transparency on source organization, license status,
       and SHA-256 content hashes.
    4. Epistemic Classification: All documentary retrievals are typed strictly as DOCUMENTARY.
"""

from datetime import date
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DocumentType(str, Enum):
    """Authoritative categories of governing motorsport documentation."""
    SPORTING_REGULATION = "SPORTING_REGULATION"
    INTERNATIONAL_SPORTING_CODE = "INTERNATIONAL_SPORTING_CODE"
    DRIVING_STANDARDS_GUIDELINES = "DRIVING_STANDARDS_GUIDELINES"
    OFFICIAL_STEWARD_DECISION = "OFFICIAL_STEWARD_DECISION"
    RACE_CONTROL_LOG = "RACE_CONTROL_LOG"
    TECHNICAL_DIRECTIVE = "TECHNICAL_DIRECTIVE"


class ProvenanceStatus(str, Enum):
    """Verification state of a documentary passage's source."""
    AUTHORITATIVE = "AUTHORITATIVE"
    VERIFIED_DOCUMENT = "VERIFIED_DOCUMENT"
    CANONICAL_DOCUMENTED = "CANONICAL_DOCUMENTED"
    PROVENANCE_INSUFFICIENT = "PROVENANCE_INSUFFICIENT"
    EFFECTIVE_DATE_UNCERTAIN = "EFFECTIVE_DATE_UNCERTAIN"


class RetrievalMethod(str, Enum):
    """Computational mechanism employed to retrieve the citation."""
    LEXICAL = "LEXICAL_BM25"
    SEMANTIC = "SEMANTIC_EMBEDDING"
    HYBRID = "HYBRID_LEXICAL_SEMANTIC"
    LEXICAL_BM25 = "LEXICAL_BM25"
    SEMANTIC_EMBEDDING = "SEMANTIC_EMBEDDING"
    HYBRID_LEXICAL_SEMANTIC = "HYBRID_LEXICAL_SEMANTIC"
    DETERMINISTIC_STATUTORY_RULE = "DETERMINISTIC_STATUTORY_RULE"
    HISTORICAL_OBSERVABLE_MATCH = "HISTORICAL_OBSERVABLE_MATCH"


class Document(BaseModel):
    """Canonical model for a complete governing document or official decision."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    document_id: str
    series: str = "Formula 1"
    season: int
    document_type: DocumentType
    document_name: str
    document_version: str
    title: str
    source_url: Optional[str] = None
    source_organization: str = "FIA World Motor Sport Council"
    publication_date: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    content_hash: str = ""
    total_articles: int = 1
    chunks: List[Any] = Field(default_factory=list)
    license: Optional[str] = "Official FIA Regulatory Publication — Educational & Stewarding Research Use"
    license_status: Optional[str] = "PUBLIC_STATUTORY_DOCUMENT"
    source_provenance: Optional[str] = "FIA_OFFICIAL_WEBSITE"
    retrieval_timestamp: Optional[str] = None
    provenance_status: ProvenanceStatus = ProvenanceStatus.AUTHORITATIVE

    @property
    def content_sha256(self) -> str:
        """Cryptographic SHA-256 hash alias."""
        return self.content_hash

    @classmethod
    def compute_hash(cls, raw_content: str) -> str:
        """Compute deterministic SHA-256 content hash."""
        return hashlib.sha256(raw_content.encode("utf-8")).hexdigest()


class DocumentChunk(BaseModel):
    """Atomic text passage linked strictly to its parent governing document."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    chunk_id: str
    document_id: str
    section: Optional[str] = None
    article_number: str
    heading: str
    text: str
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    source_url: Optional[str] = None
    content_hash: str
    document_version: Optional[str] = None
    series: str = "Formula 1"
    season: Optional[int] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    provenance_status: ProvenanceStatus = ProvenanceStatus.AUTHORITATIVE

    @property
    def content_sha256(self) -> str:
        """Alias for content_hash to support standard cryptographic naming."""
        return self.content_hash

    @property
    def title(self) -> str:
        """Alias for heading."""
        return self.heading

    @classmethod
    def compute_chunk_hash(cls, article: str, text: str) -> str:
        """Compute deterministic SHA-256 chunk hash."""
        payload = f"{article}::{text.strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SourceConflict(BaseModel):
    """Discrepancy detected between multiple governing documents or version iterations."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    conflict_type: str = "SOURCE_CONFLICT"
    issue_description: str
    conflict_description: Optional[str] = None
    document_id_a: Optional[str] = None
    document_id_b: Optional[str] = None
    article_number: Optional[str] = None
    resolution_status: str = "UNRESOLVED_DISCREPANCY"
    source_a: Dict[str, Any] = Field(default_factory=dict)
    source_b: Dict[str, Any] = Field(default_factory=dict)
    epistemic_note: str = Field(
        default="SOURCE CONFLICT DETECTED: Wording differs between applicable documents or seasons. "
        "Requires human steward interpretation; automated reconciliation is prohibited."
    )


class CitationEvidence(BaseModel):
    """Structured, citation-first documentary finding."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    claim: str = Field(..., description="Neutral factual explanation of regulatory relevance")
    source: str = Field(..., description="Governing authority (e.g. FIA)")
    document_name: str
    article_number: str
    heading: str
    verbatim_text: str
    source_url: Optional[str] = None
    evidence_type: str = "DOCUMENTARY"
    relevance_score: float
    retrieval_method: RetrievalMethod
    provenance: str
    provenance_status: ProvenanceStatus
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    effective_status: str = "EFFECTIVE"
    chunk: Optional[DocumentChunk] = None
    epistemic_notice: str = Field(
        default="CRITICAL NOTICE: Regulatory citations are documentary references only. They do not constitute an automated finding of fault, guilt, or penalty."
    )
    epistemic_warning: str = Field(
        default="DOCUMENTARY CITATION ONLY: Provides contextual regulatory standards for steward review. "
        "Does NOT infer driver guilt, fault allocation, or sporting penalties."
    )


class DocumentaryQuery(BaseModel):
    """Search request grounded strictly in observable incident characteristics."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    query: Optional[str] = None
    query_text: Optional[str] = None
    incident_type: Optional[str] = None
    corner_phase: Optional[str] = None
    relative_position: Optional[str] = None
    observable_interaction: Optional[str] = None
    track_context: Optional[str] = None
    series: str = "Formula 1"
    season: Optional[int] = 2024
    case_date: Optional[Any] = None
    article_filter: Optional[str] = None
    method: RetrievalMethod = RetrievalMethod.HYBRID
    limit: int = 5
    top_k: int = 5


class RegulationSearchResult(BaseModel):
    """Response containing citation-grounded regulatory search results."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    query_interpreted: str
    total_found: int
    citations: List[CitationEvidence]
    conflicts: List[SourceConflict] = Field(default_factory=list)
    source_conflicts: List[SourceConflict] = Field(default_factory=list)
    effective_date_filter_applied: bool = False
    season_filter_applied: bool = False
    retrieval_method: Optional[RetrievalMethod] = None
    non_adjudication_statement: str = Field(
        default="CRITICAL NON-ADJUDICATIVE NOTICE: Regulatory citations are documentary references only. They do not constitute an automated finding of fault, guilt, or penalty."
    )


class HistoricalEvidenceResult(BaseModel):
    """Documentary context from a comparable historical incident.
    
    STRICT COMPLIANCE GUARDRAIL:
        Separates observable physical similarity from documentary outcome.
        Never outputs a recommended penalty, fault score, or guilt probability.
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    case_id: str
    season: Optional[int] = None
    event: Optional[str] = None
    circuit: Optional[str] = None
    corner: Optional[str] = None
    interaction_category: Optional[str] = None
    observable_similarity_score: float = 0.0
    observable_similarity: float = 0.0
    observable_physical_dimensions: Dict[str, Any] = Field(default_factory=dict)
    similarity_features: Dict[str, Any] = Field(default_factory=dict)
    documentary_reference: Dict[str, Any] = Field(default_factory=dict)
    documentary_summary: str = ""
    official_source: str = ""
    source_url: Optional[str] = None
    documentary_articles: List[str] = Field(default_factory=list)
    evidence_type: str = "DOCUMENTARY"
    epistemic_type: str = "DOCUMENTARY"
    epistemic_notice: str = ""
    provenance_status: ProvenanceStatus = ProvenanceStatus.AUTHORITATIVE
    limitations: str = Field(
        default="Non-adjudicative historical documentary context only. Prior outcomes do not constitute binding precedent."
    )


class HistoricalSearchResult(BaseModel):
    """Collection of comparable historical incidents grounded in physical observation."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    query_case_id: Optional[str] = None
    query_description: Optional[str] = None
    query_features: Dict[str, Any] = Field(default_factory=dict)
    total_matches: int = 0
    total_comparators_considered: int = 0
    matches: List[HistoricalEvidenceResult] = Field(default_factory=list)
    non_adjudication_statement: str = Field(
        default="CRITICAL NON-ADJUDICATIVE NOTICE: Historical incident records and steward outcomes are preserved strictly as documentary reference material. Prior adjudications do NOT constitute binding legal precedent, automated fault assignments, or penalty recommendations."
    )


class RetrievalBenchmarkMetric(BaseModel):
    """Quantitative performance measurement for documentary retrieval."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    method: RetrievalMethod
    query_id: str
    query_text: str
    precision_at_1: float = 0.0
    precision_at_3: float = 0.0
    precision_at_5: float = 0.0
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    mrr: float = 0.0
    k: int = 5
    queries_evaluated: int = 1
    zero_leakage_verified: bool = True
