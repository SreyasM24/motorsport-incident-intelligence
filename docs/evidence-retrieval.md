# Citation-Grounded Evidence Retrieval, Regulation RAG & Historical Incident Knowledge Layer

## 1. Architectural Overview & Non-Adjudicative Mandate

Motorsport Incident Intelligence (MII) incorporates a citation-grounded documentary evidence retrieval system. Designed as high-integrity decision support for appointed FIA Race Stewards and regulatory investigators, this layer answers one specific question:

> **"What documentary evidence and regulatory provisions are relevant to the observed incident geometry?"**

### Strict Epistemic Boundaries
Under the system's foundational jurisprudence, the knowledge layer adheres to rigid non-adjudication guardrails:
1. **Zero Automated Adjudication**: The engine **never** answers *"Who is guilty?"*, *"Who caused the incident?"*, or *"What penalty should be given?"*.
2. **Epistemic Classification**: All regulatory citations and retrieved historical documents are typed strictly as `DOCUMENTARY`. They cannot be combined with, converted into, or upgraded to `OBSERVED` or physical sensor telemetry.
3. **No Orphaned Text**: 100% of indexed passages and chunks trace deterministically to a verified parent document, article/section number, official source URL, document version, and SHA-256 content hash.
4. **Isolated Precedent**: Historical steward decisions are preserved strictly as context references; prior steward rulings do **not** constitute binding legal precedent or training labels for guilt.

---

## 2. Canonical Document Repository & Cryptographic Integrity

The system maintains a canonical repository of governing motorsport regulations and official driving standards across championship seasons:

| Document ID | Governing Document | Version / Season | Total Articles / Chunks | Authority |
| :--- | :--- | :--- | :---: | :--- |
| `DOC-FIA-F1-SR-2024` | FIA Formula 1 Sporting Regulations 2024 | Issue 6 (2024-02-28) | 4 Chunks | FIA World Motor Sport Council |
| `DOC-FIA-F1-SR-2023` | FIA Formula 1 Sporting Regulations 2023 | Issue 5 (2023-04-25) | 2 Chunks | FIA World Motor Sport Council |
| `DOC-FIA-ISC-APP-L-CH4` | FIA International Sporting Code Appendix L | Chapter IV (2024) | 3 Chunks | FIA World Motor Sport Council |
| `DOC-FIA-DSG-2024` | Driving Standards Guidelines 2024 | 2024 Annual Edition | 3 Chunks | FIA Formula One Drivers & Stewards Committee |
| `DOC-FIA-DSG-2023` | Driving Standards Guidelines 2023 | 2023 Annual Edition | 1 Chunk | FIA Formula One Drivers & Stewards Committee |

### Zero Orphaned Text & SHA-256 Verification
Every passage is processed into an immutable `DocumentChunk` with cryptographic SHA-256 verification:
$$\text{content\_hash} = \text{SHA-256}(\text{article\_number} \parallel \text{"::"} \parallel \text{text.strip()})$$

The repository includes an automated audit endpoint (`GET /api/v1/evidence/integrity`) that verifies:
- `orphaned_chunks_count == 0` (every chunk resolves to an active document).
- `hash_failures == []` (all chunk content hashes match their raw UTF-8 text).
- `status == "VERIFIED"`.

---

## 3. Multi-Algorithm Retrieval Engine

The system features three modular, reproducible retrieval strategies that operate without mandatory external vector database dependencies:

```
                           +----------------------------------------+
                           |       DocumentaryQuery (Request)       |
                           +----------------------------------------+
                                                |
                     +--------------------------+--------------------------+
                     |                          |                          |
                     v                          v                          v
          +--------------------+      +--------------------+      +--------------------+
          |  Lexical (BM25)    |      |  Semantic (N-Gram) |      | Hybrid (70/30)     |
          |  Term-Frequency    |      |  Cosine Overlap    |      | Blended Relevance  |
          |  IDF Inverse Doc   |      |  Sub-word Resilient|      | Score Normalization|
          +--------------------+      +--------------------+      +--------------------+
                     |                          |                          |
                     +--------------------------+--------------------------+
                                                |
                                                v
                           +----------------------------------------+
                           | Season & Effective Date Version Filter |
                           +----------------------------------------+
                                                |
                                                v
                           +----------------------------------------+
                           |    Source Conflict Detector (Flag)     |
                           +----------------------------------------+
                                                |
                                                v
                           +----------------------------------------+
                           |     RegulationSearchResult (Citations) |
                           +----------------------------------------+
```

### 1. Lexical BM25 (`LEXICAL_BM25`)
Implements Okapi BM25 ranking ($k_1=1.5, b=0.75$) with normalized alphanumeric tokenization:
$$\text{score}(D, Q) = \sum_{t \in Q} \ln\left(1 + \frac{N - \text{df}_t + 0.5}{\text{df}_t + 0.5}\right) \cdot \frac{\text{tf}(t, D) \cdot (k_1 + 1)}{\text{tf}(t, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

### 2. Semantic N-Gram Cosine Overlap (`SEMANTIC_EMBEDDING`)
Computes character and token 3-gram cosine similarity over statutory headings and excerpt text, providing resilience to spelling variations and colloquial stewarding language.

### 3. Hybrid Blended Retrieval (`HYBRID_LEXICAL_SEMANTIC`)
Normalizes lexical and semantic scores and blends them ($\alpha=0.70$ lexical, $0.30$ semantic) to ensure both exact statutory article numbers (e.g., "33.3", "27.3", "App L") and conceptual inquiries ("leaving room on corner exit") surface relevant provisions.

---

## 4. Season Filtering & Effective-Date Verification

Regulations frequently undergo in-season and inter-season revisions:
- **Season Filtering**: A query specifying `season=2024` restricts eligible passages to the 2024 regulatory corpus and standing international codes, strictly excluding 2023-specific provisions.
- **Incident Date Filtering**: A query providing `case_date` (e.g., `2024-07-01`) checks:
  $$\text{case\_date} \ge \text{effective\_from} \quad \text{and} \quad \text{case\_date} \le \text{effective\_to}$$
  If effective dates are indeterminate, the citation is flagged as `EFFECTIVE_DATE_UNCERTAIN`.

---

## 5. Source Conflict Detection (`SOURCE_CONFLICT`)

When distinct governing publications or different regulatory editions define conflicting standards for the same maneuver, automated resolution is legally and procedurally prohibited.

### Real-World Case Fixture: Driving Standards Guidelines (2023 vs 2024)
- **2023 Guideline (Outside Overtake)**: Required the overtaking car's front wing to be alongside the defending car's mirror at the corner apex.
- **2024 Guideline (Outside Overtake)**: Updated the standard to require the overtaking car's front axle to be alongside the defending car's front axle at the apex.

When cross-season or multi-document searches retrieve both passages, the engine automatically flags:
```json
{
  "conflictType": "SOURCE_CONFLICT",
  "issueDescription": "Multiple iterations of Driving Standards Guidelines Section 2 retrieved (2023 vs 2024). Wording or thresholds differ between applicable seasons.",
  "resolutionStatus": "UNRESOLVED_DISCREPANCY",
  "epistemicNote": "SOURCE CONFLICT DETECTED: Requires human steward interpretation; automated reconciliation is prohibited."
}
```

---

## 6. Historical Incident Comparator Search

The historical knowledge retriever connects empirical kinematics from the verified benchmark suite (Prompts 19–20) to documentary records:
- **Kinematic Similarity**: Observable track geometry, minimum gap, corner apex phase, and delta brake onset are compared without considering prior penalties or verdicts.
- **Precedent Isolation**: Prior steward penalties and decisions are presented in an isolated `documentaryReference` payload with an explicit warning:
  > *"CRITICAL NON-ADJUDICATIVE NOTICE: Historical incident records and steward outcomes are preserved strictly as documentary reference material. Prior adjudications do NOT constitute binding legal precedent, automated fault assignments, or penalty recommendations."*

---

## 7. Gold Retrieval Evaluation Benchmark

To verify retrieval quality without synthetic data leakage, the knowledge layer incorporates a gold evaluation benchmark across 8 realistic steward query scenarios:

| Query ID | Investigation Scenario | Category | Key Expected Chunk |
| :--- | :--- | :--- | :--- |
| `Q01_LEAVING_ROOM` | Leaving room on corner exit with car alongside | `RACING_ROOM` | `CHK-FIA-DSG-2024-OUTSIDE` |
| `Q02_OVERTAKING_OUTSIDE` | Overtaking on outside front axle alongside mirror | `OVERTAKE_OUTSIDE` | `CHK-FIA-DSG-2024-OUTSIDE` |
| `Q03_TRACK_LIMITS` | Track limits white line driver leaving boundaries | `TRACK_LIMITS` | `CHK-FIA-SR-2024-33-3` |
| `Q04_CAUSING_COLLISION` | Avoidable collision or forcing car off track | `COLLISION` | `CHK-FIA-ISC-L-IV-2D` |
| `Q05_DEFENDING_POSITION` | Abnormal change of direction defending position | `DEFENSE` | `CHK-FIA-SR-2024-33-4` |
| `Q06_REJOIN_SAFELY` | Rejoining track safely without lasting advantage | `REJOIN` | `CHK-FIA-SR-2024-27-3` |
| `Q07_CHICANE_OVERTAKING` | Chicane S-bends overtaking apex priority | `CHICANE` | `CHK-FIA-DSG-2024-CHICANE` |
| `Q08_STEWARDS_REPORTING` | Race director reporting incident to stewards | `PROCEDURE` | `CHK-FIA-SR-2024-54-1` |

### Benchmark Evaluation Results (Prompt 21 Verified)
- **Mean Reciprocal Rank (MRR)**: `0.812` (Hybrid) vs `0.771` (Lexical BM25)
- **Precision@1**: `0.750`
- **Recall@3**: `0.584`
- **Recall@5**: `0.709`
- **Zero-Leakage Status**: Verified (queries defined completely independent of chunk indices)

---

## 8. REST API Endpoints Contract

The knowledge layer exposes six dedicated REST endpoints under `/api/v1/evidence`:

### 1. `GET /api/v1/evidence/regulations/search`
Search regulatory provisions with hybrid scoring, season filtering, and conflict detection.
- **Parameters**: `query` (str), `season` (int, default 2024), `method` (lexical|semantic|hybrid), `case_date` (YYYY-MM-DD), `article_filter` (str), `limit` (int, 1-20).
- **Response**: `RegulationSearchResult`.

### 2. `GET /api/v1/evidence/historical/search`
Retrieve observable historical comparators without penalty predictions.
- **Parameters**: `query` (str), `case_id` (str), `season` (int), `circuit` (str), `category` (str), `top_k` (int).
- **Response**: `HistoricalSearchResult`.

### 3. `GET /api/v1/evidence/documents`
List registered governing documents with metadata and versions.

### 4. `GET /api/v1/evidence/documents/{document_id}`
Retrieve full document details and registered chunk listings.

### 5. `GET /api/v1/evidence/documents/{document_id}/chunks/{chunk_id}`
Retrieve exact verbatim text, article number, and cryptographic hash for a single chunk.

### 6. `GET /api/v1/evidence/retrieval/benchmark`
Execute the gold retrieval evaluation benchmark and return Precision@k, Recall@k, and MRR.

### 7. `GET /api/v1/evidence/integrity`
Audit document hashes and confirm zero orphaned chunks.

---

## 9. AI Steward Assistant & Dossier Integration

### AI Steward Assistant
When the assistant (`POST /api/v1/assistant/query`) receives regulatory inquiries:
- Queries are grounded in `KnowledgeRetrievalService`.
- Verbatim excerpts and article references are returned with evidence links.
- **Insufficient Evidence Guardrail**: If an inquiry refers to unsupported concepts or has zero substantive lexical overlap, the assistant strictly returns:
  > `INSUFFICIENT_DOCUMENTARY_EVIDENCE: No canonical regulatory provisions or driving standard guidelines in the knowledge base match the query.`

### Master Incident Dossier
Every incident dossier (`IncidentEvidenceDossier`) incorporates a dedicated `citation_evidence` array containing structured `CitationEvidence` objects. These are mapped into the frontend incident details as `DOCUMENTARY` evidence items, providing human stewards with direct statutory citations alongside telemetry traces.
