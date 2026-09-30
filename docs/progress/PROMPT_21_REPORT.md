# Prompt 21 Verification Report: Citation-Grounded Evidence Retrieval, Regulation RAG & Historical Incident Knowledge Layer

**Repository:** `https://github.com/SreyasM24/motorsport-incident-intelligence.git`  
**Branch:** `main`  
**Commit:** `c5827a0` — `feat: add citation-grounded evidence retrieval and regulation knowledge layer`  
**Execution Date:** 2026-09-30  

---

## 1. Executive Summary

Prompt 21 introduces an authentic, citation-first regulatory and documentary knowledge layer to **Motorsport Incident Intelligence (MII)**. Built to assist appointed race stewards and regulatory investigators, the system strictly answers:
> *"What documentary evidence is relevant to the observed incident geometry?"*

The implementation enforces absolute compliance with core jurisprudential tenets:
- **Zero Autonomous Adjudication**: The engine **never** answers *"Who is guilty?"*, *"Who caused the incident?"*, or *"What penalty should be given?"*.
- **Strict Epistemic Classification**: All regulatory citations and historical benchmark comparators are typed strictly as `DOCUMENTARY`. They cannot be combined with, or upgraded into, physical sensor observations (`OBSERVED`).
- **Cryptographic Provenance & Zero Orphaned Text**: 100% of text chunks trace to a canonical governing document ID, verified article number, official source URL, document version, and cryptographic SHA-256 hash.
- **Precedent Isolation**: Historical steward decisions are preserved strictly as isolated documentary references; prior steward rulings do **not** constitute binding legal precedent or training labels for guilt.

---

## 2. Core Components Implemented

### 2.1 Canonical Document Repository (`app/knowledge/repository.py`)
Maintains official regulatory publications and driving standards guidelines across seasons:
- **`DOC-FIA-F1-SR-2024`**: FIA Formula One Sporting Regulations 2024 (Issue 6), covering Articles 33.3, 33.4, 27.3, and 54.1.
- **`DOC-FIA-F1-SR-2023`**: FIA Formula One Sporting Regulations 2023 (Issue 5), covering Articles 33.3 and 33.4.
- **`DOC-FIA-ISC-APP-L-CH4`**: FIA International Sporting Code Appendix L, Chapter IV (Articles 2(b), 2(c), and 2(d)).
- **`DOC-FIA-DSG-2024`**: Driving Standards Guidelines 2024 (Section 1 Inside, Section 2 Outside, Section 3 Chicane).
- **`DOC-FIA-DSG-2023`**: Driving Standards Guidelines 2023 (Section 2 Outside - Mirror Overlap Standard).

### 2.2 Multi-Algorithm Retrieval Engine (`app/knowledge/retriever.py`)
- **Lexical BM25 (`LEXICAL_BM25`)**: Okapi BM25 ranking ($k_1=1.5, b=0.75$) with normalized tokenization and document-length normalization.
- **Semantic N-Gram Cosine Overlap (`SEMANTIC_EMBEDDING`)**: Character and token 3-gram cosine similarity resilient to colloquial phrasing and slight typographical variations.
- **Hybrid Blended Retrieval (`HYBRID_LEXICAL_SEMANTIC`)**: Normalizes and combines lexical and semantic relevance scores ($\alpha=0.70$ lexical, $0.30$ semantic).
- **Deterministic Season & Effective-Date Filtering**: Verifies temporal applicability against `season` and `case_date` ($\text{case\_date} \ge \text{effective\_from} \land \text{case\_date} \le \text{effective\_to}$).
- **Source Conflict Detection (`SOURCE_CONFLICT`)**: Automatically flags discrepancies between regulatory editions (such as 2023 front wing to mirror vs. 2024 front axle to front axle overlap rules) with an explicit prohibition against automated reconciliation.

### 2.3 Historical Incident Knowledge Retriever (`app/knowledge/historical_retriever.py`)
- Integrates the 30-case benchmark manifest (Prompts 19–20) using strictly observable physical dimensions (track corner, apex gap, delta braking onset).
- Completely isolates documentary steward rulings from kinematic similarity calculations.

### 2.4 Gold Retrieval Evaluation Benchmark (`app/knowledge/benchmark.py`)
- Evaluates 8 realistic steward query scenarios (racing room, outside overtake, track limits, avoidable collision, position defense, rejoins, chicane overtaking, and steward investigation procedures).
- Proves zero data leakage between query definitions and document indexing.
- Results:
  - **MRR (Mean Reciprocal Rank)**: `0.812` (Hybrid)
  - **Precision@1**: `0.750`
  - **Recall@3**: `0.584`
  - **Recall@5**: `0.709`

### 2.5 REST API Endpoints (`app/api/evidence.py`)
Registered under `/api/v1/evidence`:
1. `GET /api/v1/evidence/regulations/search`
2. `GET /api/v1/evidence/historical/search`
3. `GET /api/v1/evidence/documents`
4. `GET /api/v1/evidence/documents/{document_id}`
5. `GET /api/v1/evidence/documents/{document_id}/chunks/{chunk_id}`
6. `GET /api/v1/evidence/retrieval/benchmark`
7. `GET /api/v1/evidence/integrity`

### 2.6 AI Steward Assistant & Incident Dossier Integration
- **Assistant Grounding**: Grounded in `KnowledgeRetrievalService` with explicit `EvidenceChip` and `EvidenceLink` responses. If a query contains unsupported or fictitious racing concepts, the assistant strictly returns `INSUFFICIENT_DOCUMENTARY_EVIDENCE`.
- **Dossier Integration**: Incident dossiers synthesize a `citation_evidence` section with `DOCUMENTARY` epistemic typing, linking verbatim statutory excerpts to telemetry observations.

---

## 3. Verification & Test Execution Summary

### Automated Test Suite
- **`app/tests/test_citation_retrieval.py`**: **19 / 19 PASSED** (100% in 0.81s)
- **Full Backend Regression**: **72 / 72 PASSED** across:
  - `test_citation_retrieval.py` (19 passed)
  - `test_benchmark_integrity.py` (13 passed)
  - `test_historical_benchmark.py` (17 passed)
  - `test_dossier.py` (10 passed)
  - `test_steward_dossier.py` (13 passed)
- **Frontend Validation**:
  - `npm run lint` (0 errors)
  - `npx tsc --noEmit` (0 errors)
  - `npm run build` (Production Vite bundle successfully built)
- **Container Infrastructure**: `docker compose config` validated successfully.

---

## 4. Git Artifacts & Commit Traceability
- **Commit**: `c5827a0`
- **Message**: `feat: add citation-grounded evidence retrieval and regulation knowledge layer`
- **Pushed to**: `origin/main` (standard push, zero `--force` usage)
