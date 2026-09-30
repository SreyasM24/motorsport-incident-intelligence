"""Knowledge Retrieval Service — Unified API and Pipeline Orchestrator.

Provides high-level methods for regulatory search, document inspection,
historical incident retrieval, source conflict detection, and benchmark evaluations.
"""

from typing import Any, Dict, List, Optional
from datetime import date

from app.knowledge.models import (
    Document,
    DocumentChunk,
    DocumentaryQuery,
    HistoricalSearchResult,
    RegulationSearchResult,
    RetrievalMethod,
)
from app.knowledge.repository import DocumentRepository
from app.knowledge.retriever import KnowledgeRetrievalEngine
from app.knowledge.historical_retriever import HistoricalIncidentKnowledgeRetriever
from app.knowledge.benchmark import RetrievalBenchmarkEvaluator, RetrievalBenchmarkReport


class KnowledgeRetrievalService:
    """Singleton service for citation-grounded documentary evidence retrieval."""

    _instance: Optional["KnowledgeRetrievalService"] = None

    def __init__(self):
        self.repository = DocumentRepository()
        self.engine = KnowledgeRetrievalEngine(self.repository)
        self.historical_retriever = HistoricalIncidentKnowledgeRetriever()
        self.evaluator = RetrievalBenchmarkEvaluator(self.engine, self.repository)

    @classmethod
    def get_instance(cls) -> "KnowledgeRetrievalService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def search_regulations(
        self,
        query: str,
        season: Optional[int] = 2024,
        method: RetrievalMethod = RetrievalMethod.HYBRID,
        case_date: Optional[date] = None,
        article_filter: Optional[str] = None,
        limit: int = 5,
    ) -> RegulationSearchResult:
        """Search regulatory documents and return citation-grounded passages."""
        doc_query = DocumentaryQuery(
            query=query,
            season=season,
            method=method,
            case_date=case_date,
            article_filter=article_filter,
            limit=limit,
        )
        return self.engine.search_regulations(doc_query)

    def search_historical(
        self,
        query: str,
        season: Optional[int] = None,
        circuit: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> HistoricalSearchResult:
        """Search historical incident records with strict non-adjudication isolation."""
        return self.historical_retriever.search_historical_cases(
            query=query,
            season=season,
            circuit=circuit,
            category=category,
            top_k=top_k,
        )

    def get_comparable_incidents(
        self,
        case_id: str,
        top_k: int = 3,
    ) -> HistoricalSearchResult:
        """Find comparable cases based on observable kinematics for a given case ID."""
        return self.historical_retriever.retrieve_by_case_id(
            case_id=case_id,
            top_k=top_k,
        )

    def list_documents(
        self,
        season: Optional[int] = None,
        document_type: Optional[str] = None,
    ) -> List[Document]:
        """List all canonical documents in the repository."""
        return self.repository.list_documents(
            season=season,
            document_type=document_type,
        )

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get full metadata and chunks for a document."""
        return self.repository.get_document(document_id)

    def get_chunk(self, document_id: str, chunk_id: str) -> Optional[DocumentChunk]:
        """Get a specific chunk by document ID and chunk ID."""
        return self.repository.get_chunk(document_id, chunk_id)

    def run_benchmark(self) -> RetrievalBenchmarkReport:
        """Run the gold standard retrieval evaluation benchmark."""
        return self.evaluator.run_benchmark()

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify provenance and hash integrity of all indexed documents and chunks."""
        return self.repository.verify_integrity()


def get_knowledge_service() -> KnowledgeRetrievalService:
    """Dependency helper for FastAPI endpoints and services."""
    return KnowledgeRetrievalService.get_instance()
