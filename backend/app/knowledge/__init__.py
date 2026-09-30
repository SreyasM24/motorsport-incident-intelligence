"""Knowledge and Citation-Grounded Evidence Retrieval Package (Prompt 21).

Provides:
- Canonical regulatory document repository (FIA Sporting Regulations, ISC App L, Driving Standards)
- Provenance verification and SHA-256 chunk hashing
- Lexical BM25 and Semantic Overlap retrieval engines
- Version conflict detection (SOURCE_CONFLICT)
- Historical incident comparator search with physical/documentary isolation
- Gold retrieval benchmark evaluation (Precision@k, Recall@k, MRR)
"""

from app.knowledge.models import (
    Document,
    DocumentChunk,
    DocumentType,
    ProvenanceStatus,
    RetrievalMethod,
    CitationEvidence,
    SourceConflict,
    DocumentaryQuery,
    RegulationSearchResult,
    HistoricalEvidenceResult,
    HistoricalSearchResult,
    RetrievalBenchmarkMetric,
)
from app.knowledge.repository import DocumentRepository
from app.knowledge.retriever import (
    LexicalRetriever,
    SemanticRetriever,
    HybridRetriever,
    KnowledgeRetrievalEngine,
)
from app.knowledge.historical_retriever import HistoricalIncidentKnowledgeRetriever
from app.knowledge.benchmark import (
    GOLD_BENCHMARK_QUERIES,
    GoldQueryGroundTruth,
    RetrievalBenchmarkEvaluator,
    RetrievalBenchmarkReport,
)
from app.knowledge.service import KnowledgeRetrievalService, get_knowledge_service

__all__ = [
    "Document",
    "DocumentChunk",
    "DocumentType",
    "ProvenanceStatus",
    "RetrievalMethod",
    "CitationEvidence",
    "SourceConflict",
    "DocumentaryQuery",
    "RegulationSearchResult",
    "HistoricalEvidenceResult",
    "HistoricalSearchResult",
    "RetrievalBenchmarkMetric",
    "DocumentRepository",
    "LexicalRetriever",
    "SemanticRetriever",
    "HybridRetriever",
    "KnowledgeRetrievalEngine",
    "HistoricalIncidentKnowledgeRetriever",
    "GOLD_BENCHMARK_QUERIES",
    "GoldQueryGroundTruth",
    "RetrievalBenchmarkEvaluator",
    "RetrievalBenchmarkReport",
    "KnowledgeRetrievalService",
    "get_knowledge_service",
]
