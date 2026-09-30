"""API router for citation-grounded documentary evidence retrieval, regulations, and benchmark."""

from typing import Any, Dict, List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.knowledge.models import (
    Document,
    DocumentChunk,
    HistoricalSearchResult,
    RegulationSearchResult,
    RetrievalMethod,
)
from app.knowledge.benchmark import RetrievalBenchmarkReport
from app.knowledge.service import KnowledgeRetrievalService, get_knowledge_service
from app.benchmark.comparator import HistoricalComparisonResponse

router = APIRouter(prefix="/evidence", tags=["Evidence & Knowledge Retrieval"])


@router.get(
    "/regulations/search",
    response_model=RegulationSearchResult,
    summary="Search regulatory documents with citation grounding and conflict detection",
)
def search_regulations(
    query: str = Query(..., description="Query regarding driving standards, sporting regulations, or rules"),
    season: Optional[int] = Query(default=2024, description="Championship season filter"),
    method: RetrievalMethod = Query(default=RetrievalMethod.HYBRID, description="Retrieval method (lexical, semantic, hybrid)"),
    case_date: Optional[date] = Query(default=None, description="Incident date for temporal version applicability checking"),
    article_filter: Optional[str] = Query(default=None, description="Optional article substring filter (e.g. '33.3')"),
    limit: int = Query(default=5, ge=1, le=20, description="Max citations returned"),
    service: KnowledgeRetrievalService = Depends(get_knowledge_service),
) -> RegulationSearchResult:
    """Retrieve verified regulatory passages grounded in canonical source documents."""
    return service.search_regulations(
        query=query,
        season=season,
        method=method,
        case_date=case_date,
        article_filter=article_filter,
        limit=limit,
    )


@router.get(
    "/historical/search",
    response_model=HistoricalSearchResult,
    summary="Search verified historical cases with strict non-adjudication isolation",
)
def search_historical_incidents(
    query: Optional[str] = Query(default=None, description="Observable incident search text"),
    case_id: Optional[str] = Query(default=None, description="Historical case ID to find kinematically comparable matches for"),
    season: Optional[int] = Query(default=None, description="Championship season filter"),
    circuit: Optional[str] = Query(default=None, description="Circuit name filter"),
    category: Optional[str] = Query(default=None, description="Incident category filter (e.g., FORCING_OFF_TRACK)"),
    top_k: int = Query(default=5, ge=1, le=20, description="Maximum number of historical records to return"),
    service: KnowledgeRetrievalService = Depends(get_knowledge_service),
) -> HistoricalSearchResult:
    """Retrieve empirically comparable historical cases without predicting penalties or guilt."""
    if case_id:
        return service.get_comparable_incidents(case_id=case_id, top_k=top_k)
    return service.search_historical(
        query=query or "",
        season=season,
        circuit=circuit,
        category=category,
        top_k=top_k,
    )


@router.get(
    "/historical/compare/{candidate_id}",
    response_model=HistoricalComparisonResponse,
    summary="Explainable historical case comparison with observable kinematics and side-by-side analysis",
)
def compare_historical_case(
    candidate_id: str,
    top_k: int = Query(default=3, ge=1, le=10, description="Maximum number of comparable cases to return"),
    circuit: Optional[str] = Query(default=None, description="Optional circuit filter"),
    season: Optional[int] = Query(default=None, description="Optional season filter"),
    min_similarity: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum observable similarity threshold"),
    service: KnowledgeRetrievalService = Depends(get_knowledge_service),
) -> HistoricalComparisonResponse:
    """Retrieve explainable historical comparators grounded in observable kinematics with side-by-side metrics."""
    return service.compare_case(
        candidate_id=candidate_id,
        top_k=top_k,
        circuit=circuit,
        season=season,
        min_similarity=min_similarity,
    )


@router.get(
    "/documents",
    response_model=List[Document],
    summary="List all canonical documents in the repository",
)
def list_documents(
    season: Optional[int] = Query(default=None, description="Filter by championship season"),
    document_type: Optional[str] = Query(default=None, description="Filter by document type"),
    service: KnowledgeRetrievalService = Depends(get_knowledge_service),
) -> List[Document]:
    """Return all official regulatory documents registered in the knowledge layer."""
    return service.list_documents(season=season, document_type=document_type)


@router.get(
    "/documents/{document_id}",
    response_model=Document,
    summary="Get document metadata and chunk index",
)
def get_document(
    document_id: str,
    service: KnowledgeRetrievalService = Depends(get_knowledge_service),
) -> Document:
    """Retrieve full document record with verification hashes and child chunk references."""
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    return doc


@router.get(
    "/documents/{document_id}/chunks/{chunk_id}",
    response_model=DocumentChunk,
    summary="Get exact chunk text, article number, and SHA-256 hash",
)
def get_chunk(
    document_id: str,
    chunk_id: str,
    service: KnowledgeRetrievalService = Depends(get_knowledge_service),
) -> DocumentChunk:
    """Retrieve a specific chunk with zero orphaned text guarantees and cryptographic hash."""
    chunk = service.get_chunk(document_id, chunk_id)
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunk '{chunk_id}' not found in document '{document_id}'.",
        )
    return chunk


@router.get(
    "/retrieval/benchmark",
    response_model=RetrievalBenchmarkReport,
    summary="Run gold standard retrieval benchmark (Precision@k, Recall@k, MRR)",
)
def run_retrieval_benchmark(
    service: KnowledgeRetrievalService = Depends(get_knowledge_service),
) -> RetrievalBenchmarkReport:
    """Execute gold retrieval evaluation benchmark verifying zero data leakage."""
    return service.run_benchmark()


@router.get(
    "/integrity",
    response_model=Dict[str, Any],
    summary="Audit repository hash integrity and check for orphaned text",
)
def verify_knowledge_integrity(
    service: KnowledgeRetrievalService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    """Verify cryptographic SHA-256 hashes and validate that 100% of chunks trace to canonical documents."""
    return service.verify_integrity()
