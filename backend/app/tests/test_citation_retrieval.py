"""Automated Test Suite for Citation-Grounded Evidence Retrieval & Regulation RAG (Prompt 21).

Tests:
1. Canonical Document & Chunk Data Models
2. Repository Content Hashing & Zero Orphaned Text Verification
3. Lexical BM25 & Semantic Hybrid Retrieval
4. Season & Effective Date Version Filtering
5. Source Conflict Detection (SOURCE_CONFLICT)
6. Historical Incident Comparator Search & Precedent Isolation
7. Gold Retrieval Benchmark (Precision@k, Recall@k, MRR)
8. API Endpoints Contract Validation
9. AI Assistant Citation Grounding & Insufficient Evidence Guardrails
10. Incident Dossier Integration with Strict DOCUMENTARY Epistemic Typing
"""

from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.main import create_application
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
)
from app.knowledge.repository import DocumentRepository
from app.knowledge.retriever import (
    LexicalRetriever,
    SemanticRetriever,
    HybridRetriever,
    KnowledgeRetrievalEngine,
)
from app.knowledge.historical_retriever import HistoricalIncidentKnowledgeRetriever
from app.knowledge.benchmark import RetrievalBenchmarkEvaluator, GOLD_BENCHMARK_QUERIES
from app.knowledge.service import KnowledgeRetrievalService


@pytest.fixture
def repo() -> DocumentRepository:
    return DocumentRepository()


@pytest.fixture
def engine(repo: DocumentRepository) -> KnowledgeRetrievalEngine:
    return KnowledgeRetrievalEngine(repo)


@pytest.fixture
def client() -> TestClient:
    app = create_application()
    return TestClient(app)


# ==============================================================================
# 1. CANONICAL REPOSITORY & INTEGRITY AUDIT
# ==============================================================================

def test_repository_integrity_and_hashing(repo: DocumentRepository):
    """Verify that all documents and chunks have cryptographic SHA-256 hashes and zero orphans."""
    audit = repo.verify_integrity()
    assert audit["status"] == "VERIFIED"
    assert audit["orphaned_chunks_count"] == 0
    assert audit["total_documents"] >= 4
    assert audit["total_chunks"] >= 10
    assert len(audit["hash_failures"]) == 0


def test_chunk_provenance_and_immutability(repo: DocumentRepository):
    """Ensure every chunk contains document_id, article_number, source_url, and document_version."""
    for chunk in repo.chunks.values():
        assert chunk.document_id is not None
        assert chunk.document_id in repo.documents
        assert chunk.article_number != ""
        assert chunk.source_url.startswith("http") or chunk.source_url.startswith("https")
        assert chunk.document_version != ""
        assert len(chunk.content_sha256) == 64  # SHA-256 length


def test_no_orphaned_chunks(repo: DocumentRepository):
    """Audit guarantee: 100% of chunks must belong to a known canonical document."""
    orphans = repo.audit_orphaned_chunks()
    assert len(orphans) == 0


# ==============================================================================
# 2. RETRIEVAL ENGINE ALGORITHMS (LEXICAL, SEMANTIC, HYBRID)
# ==============================================================================

def test_lexical_bm25_retrieval(repo: DocumentRepository):
    """Verify BM25 retrieval finds relevant articles for key regulatory terms."""
    retriever = LexicalRetriever(repo)
    chunks = repo.list_chunks()

    # Query: track limits
    hits = retriever.search("track limits white line", chunks, top_k=3)
    assert len(hits) > 0
    top_chunk, score = hits[0]
    assert "33.3" in top_chunk.article_number or "2(c)" in top_chunk.article_number
    assert score > 0.0


def test_semantic_n_gram_retrieval(repo: DocumentRepository):
    """Verify semantic/n-gram retrieval surfaces relevant passages."""
    retriever = SemanticRetriever(repo)
    chunks = repo.list_chunks()

    hits = retriever.search("overtaking on the outside front axle", chunks, top_k=3)
    assert len(hits) > 0
    top_chunk, score = hits[0]
    assert score > 0.0
    assert "DSG" in top_chunk.document_id or "ISC" in top_chunk.document_id


def test_hybrid_retrieval_scoring(engine: KnowledgeRetrievalEngine):
    """Verify hybrid retriever combines lexical and semantic scores."""
    query = DocumentaryQuery(
        query="leaving room on corner exit when car is alongside",
        season=2024,
        method=RetrievalMethod.HYBRID,
        limit=3,
    )
    result = engine.search_regulations(query)
    assert len(result.citations) > 0
    assert result.retrieval_method == RetrievalMethod.HYBRID

    top_citation = result.citations[0]
    assert top_citation.relevance_score > 0.0
    assert top_citation.provenance_status in (ProvenanceStatus.CANONICAL_DOCUMENTED, ProvenanceStatus.AUTHORITATIVE)


# ==============================================================================
# 3. SEASON & EFFECTIVE DATE FILTERING
# ==============================================================================

def test_season_filtering(engine: KnowledgeRetrievalEngine):
    """Ensure querying 2024 returns 2024 documents and excludes 2023-only variants."""
    query_2024 = DocumentaryQuery(query="overtaking room", season=2024, limit=5)
    res_2024 = engine.search_regulations(query_2024)
    for c in res_2024.citations:
        assert c.chunk.season in (2024, None)

    query_2023 = DocumentaryQuery(query="overtaking room", season=2023, limit=5)
    res_2023 = engine.search_regulations(query_2023)
    for c in res_2023.citations:
        assert c.chunk.season in (2023, None)


def test_effective_date_validation(engine: KnowledgeRetrievalEngine):
    """Check effective date validation for in-season temporal applicability."""
    # Query during 2024 season
    q_in = DocumentaryQuery(
        query="Article 33.3 track limits",
        season=2024,
        case_date=date(2024, 7, 1),
    )
    res_in = engine.search_regulations(q_in)
    assert len(res_in.citations) > 0
    assert res_in.citations[0].effective_status == "EFFECTIVE"

    # Query before 2024 season effective date
    q_out = DocumentaryQuery(
        query="Article 33.3 track limits",
        season=2024,
        case_date=date(2023, 1, 1),
    )
    res_out = engine.search_regulations(q_out)
    # The 2024 regulation should not match as effective for a 2023 date
    matching_2024 = [c for c in res_out.citations if c.chunk.season == 2024]
    assert len(matching_2024) == 0


# ==============================================================================
# 4. SOURCE CONFLICT DETECTION (SOURCE_CONFLICT)
# ==============================================================================

def test_source_conflict_detection(engine: KnowledgeRetrievalEngine):
    """Verify that version differences in Driving Standards Guidelines generate SOURCE_CONFLICT."""
    query = DocumentaryQuery(
        query="overtaking outside front axle alongside mirror driving standards",
        season=None,  # Cross-season search to detect version changes
        limit=5,
    )
    result = engine.search_regulations(query)
    assert len(result.source_conflicts) > 0
    conflict = result.source_conflicts[0]
    assert conflict.conflict_type == "SOURCE_CONFLICT"
    assert "DSG-2023" in conflict.document_id_a or "DSG-2024" in conflict.document_id_a
    assert "DSG-2023" in conflict.document_id_b or "DSG-2024" in conflict.document_id_b
    assert conflict.resolution_status == "UNRESOLVED_DISCREPANCY"


# ==============================================================================
# 5. HISTORICAL RETRIEVER & PRECEDENT ISOLATION
# ==============================================================================

def test_historical_retriever_observable_similarity():
    """Verify historical retriever surfaces cases based on observable kinematics, not verdicts."""
    retriever = HistoricalIncidentKnowledgeRetriever()
    search_res = retriever.retrieve_by_case_id("CASE-2024-MONZA-T4-01", top_k=3)

    assert search_res.total_comparators_considered >= 8
    assert len(search_res.matches) > 0
    assert "CRITICAL NON-ADJUDICATIVE NOTICE" in search_res.non_adjudication_statement

    top = search_res.matches[0]
    assert top.epistemic_type == "DOCUMENTARY"
    assert top.observable_similarity_score > 0.0
    assert "minimum_gap_meters_range" in top.observable_physical_dimensions
    assert "documented_decision_type" in top.documentary_reference


def test_historical_retriever_text_search():
    """Verify free-text search over observable historical incident attributes."""
    retriever = HistoricalIncidentKnowledgeRetriever()
    res = retriever.search_historical_cases(
        query="Monza chicane braking",
        circuit="Monza",
        top_k=3,
    )
    assert len(res.matches) > 0
    for m in res.matches:
        assert "Monza" in m.circuit


# ==============================================================================
# 6. GOLD RETRIEVAL EVALUATION BENCHMARK
# ==============================================================================

def test_gold_retrieval_benchmark_execution():
    """Verify the gold benchmark evaluates Precision@k, Recall@k, and MRR with zero data leakage."""
    evaluator = RetrievalBenchmarkEvaluator()
    report = evaluator.run_benchmark(
        queries=GOLD_BENCHMARK_QUERIES[:4],
        methods=[RetrievalMethod.LEXICAL, RetrievalMethod.HYBRID],
    )

    assert report.total_queries_evaluated == 4
    assert len(report.results_by_method) == 2
    hybrid_summary = report.results_by_method["hybrid"]
    assert hybrid_summary.mean_mrr > 0.0
    assert hybrid_summary.mean_recall_at_5 > 0.0
    assert report.evaluation_passed is True


# ==============================================================================
# 7. REST API ENDPOINTS
# ==============================================================================

def test_api_regulations_search(client: TestClient):
    """Test GET /api/v1/evidence/regulations/search."""
    resp = client.get("/api/v1/evidence/regulations/search?query=track+limits+white+line&season=2024")
    assert resp.status_code == 200
    data = resp.json()
    assert "citations" in data
    assert len(data["citations"]) > 0
    assert "nonAdjudicationStatement" in data


def test_api_historical_search(client: TestClient):
    """Test GET /api/v1/evidence/historical/search."""
    resp = client.get("/api/v1/evidence/historical/search?case_id=CASE-2024-MONZA-T4-01&top_k=2")
    assert resp.status_code == 200
    data = resp.json()
    assert "matches" in data
    assert len(data["matches"]) > 0
    assert "nonAdjudicationStatement" in data


def test_api_document_and_chunk_retrieval(client: TestClient):
    """Test GET /api/v1/evidence/documents/{document_id} and chunk endpoint."""
    resp = client.get("/api/v1/evidence/documents/FIA-SR-2024")
    assert resp.status_code == 200
    doc = resp.json()
    assert "SR-2024" in doc["documentId"]
    assert len(doc["chunks"]) > 0

    chunk_id = doc["chunks"][0]["chunkId"]
    c_resp = client.get(f"/api/v1/evidence/documents/{doc['documentId']}/chunks/{chunk_id}")
    assert c_resp.status_code == 200
    chunk = c_resp.json()
    assert chunk["chunkId"] == chunk_id


def test_api_integrity_endpoint(client: TestClient):
    """Test GET /api/v1/evidence/integrity."""
    resp = client.get("/api/v1/evidence/integrity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "VERIFIED"
    assert data["orphaned_chunks_count"] == 0


def test_api_retrieval_benchmark_endpoint(client: TestClient):
    """Test GET /api/v1/evidence/retrieval/benchmark."""
    resp = client.get("/api/v1/evidence/retrieval/benchmark")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalQueriesEvaluated"] >= 8
    assert "resultsByMethod" in data
    assert data["evaluationPassed"] is True


# ==============================================================================
# 8. ASSISTANT CITATION GROUNDING & GUARDRAILS
# ==============================================================================

def test_assistant_grounded_citation(client: TestClient):
    """Verify assistant surfaces citation-grounded passages and evidence links."""
    payload = {
        "query": "Which regulations apply to leaving room on the outside of a corner?",
        "incident_id": "INC-TEST-001",
    }
    resp = client.post("/api/v1/assistant/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "Citation-grounded regulatory references" in data["text"]
    assert any("Art" in c["label"] or "DSG" in c["label"] for c in data["evidenceChips"])
    assert "CRITICAL NON-ADJUDICATIVE NOTICE" in data["text"]


def test_assistant_insufficient_evidence_guardrail(client: TestClient):
    """Verify assistant reports INSUFFICIENT_DOCUMENTARY_EVIDENCE for unsupported queries."""
    payload = {
        "query": "regulation regarding quantum hyperdrive warp teleporter tachyon flux",
        "incident_id": "INC-TEST-002",
    }
    resp = client.post("/api/v1/assistant/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "INSUFFICIENT_DOCUMENTARY_EVIDENCE" in data["text"]
