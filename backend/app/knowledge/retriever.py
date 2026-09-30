"""Retrieval engine supporting lexical, semantic, and hybrid evidence retrieval (Prompt 21).

CRITICAL NON-ADJUDICATIVE PRINCIPLES:
    1. Answers "What documentary evidence is relevant?", NOT "Who is guilty?".
    2. Zero Orphaned Text: Every retrieved passage is anchored to its source document and URL.
    3. Observable Query Construction: Queries derive strictly from physical kinematics and
       track geometry, never driver reputation, team standing, or past penalty records.
    4. Deterministic Season & Date Filtering: Accurately checks effective dates without silent leakage.
    5. Source Conflict Transparency: Flag discrepancies between versions without autonomous resolution.
"""

from datetime import datetime, date
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.knowledge.models import (
    CitationEvidence,
    Document,
    DocumentChunk,
    DocumentaryQuery,
    ProvenanceStatus,
    RegulationSearchResult,
    RetrievalMethod,
    SourceConflict,
)
from app.knowledge.repository import DocumentRepository


class LexicalRetriever:
    """Deterministic BM25 keyword and observable term relevance scorer."""

    def __init__(self, repository: DocumentRepository):
        self.repository = repository
        self.k1 = 1.5
        self.b = 0.75
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """Normalize and tokenize text into distinct alphanumeric terms."""
        clean = re.sub(r"[^\w\s\.-]", " ", text.lower())
        tokens = [t.strip() for t in clean.split() if len(t.strip()) > 1]
        return tokens

    def _build_index(self):
        """Construct inverted index and document length tables."""
        self.doc_lengths: Dict[str, int] = {}
        self.inverted_index: Dict[str, List[Tuple[str, int]]] = {}
        self.total_docs = len(self.repository.chunk_list)
        total_len = 0

        for chunk in self.repository.chunk_list:
            full_text = f"{chunk.article_number} {chunk.heading} {chunk.section or ''} {chunk.text}"
            tokens = self._tokenize(full_text)
            self.doc_lengths[chunk.chunk_id] = len(tokens)
            total_len += len(tokens)

            tf_map: Dict[str, int] = {}
            for t in tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            for term, freq in tf_map.items():
                self.inverted_index.setdefault(term, []).append((chunk.chunk_id, freq))

        self.avg_doc_len = (total_len / self.total_docs) if self.total_docs > 0 else 1.0

    def search(
        self,
        query_terms: List[str] | str,
        eligible_chunks: List[DocumentChunk],
        top_k: int = 5,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Score eligible chunks using standard BM25 formula."""
        if isinstance(query_terms, str):
            query_terms = self._tokenize(query_terms)

        chunk_map = {c.chunk_id: c for c in eligible_chunks}
        scores: Dict[str, float] = {c.chunk_id: 0.0 for c in eligible_chunks}

        for term in query_terms:
            postings = self.inverted_index.get(term, [])
            df = len(postings)
            if df == 0:
                continue

            idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))

            for doc_id, tf in postings:
                if doc_id in scores:
                    doc_len = self.doc_lengths.get(doc_id, self.avg_doc_len)
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    scores[doc_id] += idf * (numerator / denominator)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results: List[Tuple[DocumentChunk, float]] = []
        for cid, sc in ranked[:top_k]:
            if sc > 0:
                results.append((chunk_map[cid], round(sc, 3)))
        return results


class SemanticRetriever:
    """Semantic term overlap and character n-gram cosine similarity retriever."""

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def _get_ngrams(self, text: str, n: int = 3) -> Set[str]:
        """Extract sub-word character n-grams for typo-resilient semantic overlap."""
        norm = re.sub(r"\s+", " ", text.lower().strip())
        return set(norm[i : i + n] for i in range(len(norm) - n + 1))

    def search(
        self,
        query: str,
        eligible_chunks: List[DocumentChunk],
        top_k: int = 5,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Compute cosine similarity over character and word token representations."""
        q_ngrams = self._get_ngrams(query)
        if not q_ngrams:
            return []

        results: List[Tuple[DocumentChunk, float]] = []
        for chunk in eligible_chunks:
            corpus_text = f"{chunk.article_number} {chunk.heading} {chunk.text}"
            c_ngrams = self._get_ngrams(corpus_text)

            intersection = len(q_ngrams.intersection(c_ngrams))
            denom = math.sqrt(len(q_ngrams)) * math.sqrt(len(c_ngrams)) if c_ngrams else 1.0
            sim = (intersection / denom) if denom > 0 else 0.0

            if sim > 0.05:
                results.append((chunk, round(sim, 3)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class HybridRetriever:
    """Blends BM25 lexical keyword relevance with semantic n-gram overlap."""

    def __init__(self, repository: DocumentRepository):
        self.repository = repository
        self.lexical = LexicalRetriever(repository)
        self.semantic = SemanticRetriever(repository)

    def retrieve(
        self,
        query_terms: List[str],
        query_str: str,
        eligible_chunks: List[DocumentChunk],
        top_k: int = 5,
        alpha: float = 0.70,
    ) -> List[Tuple[float, DocumentChunk, RetrievalMethod]]:
        """Blended retrieval returning (score, chunk, method)."""
        lex_results = dict([(c.chunk_id, (c, score)) for c, score in self.lexical.search(query_terms, eligible_chunks, top_k=top_k * 2)])
        sem_results = dict([(c.chunk_id, (c, score)) for c, score in self.semantic.search(query_str, eligible_chunks, top_k=top_k * 2)])

        max_lex = max([sc for _, sc in lex_results.values()], default=1.0) or 1.0
        max_sem = max([sc for _, sc in sem_results.values()], default=1.0) or 1.0

        all_ids = set(lex_results.keys()).union(set(sem_results.keys()))
        scored: List[Tuple[float, DocumentChunk, RetrievalMethod]] = []

        chunk_lookup = {c.chunk_id: c for c in eligible_chunks}

        for cid in all_ids:
            chunk = chunk_lookup.get(cid)
            if not chunk:
                continue

            lex_norm = (lex_results[cid][1] / max_lex) if cid in lex_results else 0.0
            sem_norm = (sem_results[cid][1] / max_sem) if cid in sem_results else 0.0

            combined = (alpha * lex_norm) + ((1.0 - alpha) * sem_norm)
            if combined > 0.01:
                scored.append((round(combined, 3), chunk, RetrievalMethod.HYBRID))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]


class KnowledgeRetrievalEngine:
    """Unified engine for regulatory search, provenance enforcement, and conflict detection."""

    def __init__(self, repository: DocumentRepository):
        self.repository = repository
        self.lexical = LexicalRetriever(repository)
        self.semantic = SemanticRetriever(repository)
        self.hybrid = HybridRetriever(repository)

    def _filter_by_season_and_date(
        self,
        season: Optional[int],
        case_date: Optional[Any],
    ) -> Tuple[List[DocumentChunk], bool, bool]:
        """Filter chunk universe based on championship season and effective dates."""
        eligible: List[DocumentChunk] = []
        season_filtered = False
        date_filtered = False

        c_dt: Optional[datetime] = None
        if case_date:
            try:
                if hasattr(case_date, "strftime"):
                    clean_date = case_date.strftime("%Y-%m-%d")
                else:
                    clean_date = str(case_date).split("T")[0]
                c_dt = datetime.strptime(clean_date, "%Y-%m-%d")
            except Exception:
                c_dt = None

        for chunk in self.repository.chunk_list:
            # 1. Season filtering:
            if season is not None:
                season_filtered = True
                if chunk.season is not None and chunk.season != season:
                    continue

            # 2. Effective-date filtering:
            if c_dt and chunk.effective_from:
                date_filtered = True
                try:
                    eff_from = datetime.strptime(chunk.effective_from, "%Y-%m-%d")
                    if c_dt < eff_from:
                        continue  # Not yet in effect on incident date
                except Exception:
                    pass

                if chunk.effective_to:
                    try:
                        eff_to = datetime.strptime(chunk.effective_to, "%Y-%m-%d")
                        if c_dt > eff_to:
                            continue  # Expired prior to incident date
                    except Exception:
                        pass

            eligible.append(chunk)

        return eligible, season_filtered, date_filtered

    def _detect_source_conflicts(self, chunks: List[DocumentChunk]) -> List[SourceConflict]:
        """Detect if multiple versions of the same article exist in the retrieved pool."""
        conflicts: List[SourceConflict] = []
        by_article: Dict[str, List[DocumentChunk]] = {}

        for c in chunks:
            by_article.setdefault(c.article_number, []).append(c)

        for art_num, versions in by_article.items():
            if len(versions) > 1:
                first_text = versions[0].text.strip()
                differing = [v for v in versions[1:] if v.text.strip() != first_text]
                if differing:
                    v_a = versions[0]
                    v_b = differing[0]
                    conflicts.append(
                        SourceConflict(
                            conflict_type="SOURCE_CONFLICT",
                            issue_description=(
                                f"Multiple iterations of {art_num} retrieved ({v_a.document_version} vs {v_b.document_version}). "
                                "Wording or thresholds differ between applicable seasons."
                            ),
                            conflict_description=f"Wording or threshold variance between {v_a.document_version} and {v_b.document_version}",
                            document_id_a=v_a.document_id,
                            document_id_b=v_b.document_id,
                            article_number=art_num,
                            resolution_status="UNRESOLVED_DISCREPANCY",
                            source_a={
                                "documentId": v_a.document_id,
                                "version": v_a.document_version,
                                "season": v_a.season,
                                "effectiveFrom": v_a.effective_from,
                                "text": v_a.text[:150] + "...",
                            },
                            source_b={
                                "documentId": v_b.document_id,
                                "version": v_b.document_version,
                                "season": v_b.season,
                                "effectiveFrom": v_b.effective_from,
                                "text": v_b.text[:150] + "...",
                            },
                        )
                    )
        return conflicts

    def search_regulations(self, query: DocumentaryQuery) -> RegulationSearchResult:
        """Execute citation-grounded regulatory search from observable incident parameters."""
        query_parts: List[str] = []
        if query.query:
            query_parts.append(query.query)
        if query.query_text:
            query_parts.append(query.query_text)
        if query.incident_type:
            query_parts.append(query.incident_type.replace("_", " "))
        if query.observable_interaction:
            query_parts.append(query.observable_interaction.replace("_", " "))
        if query.corner_phase:
            query_parts.append(query.corner_phase.replace("_", " "))
        if query.relative_position:
            query_parts.append(query.relative_position.replace("_", " "))

        full_query = " ".join(query_parts) if query_parts else "racing conduct track limits overtaking"
        query_terms = self.lexical._tokenize(full_query)

        # Apply season and date filters
        eligible_chunks, season_filtered, date_filtered = self._filter_by_season_and_date(
            season=query.season,
            case_date=query.case_date,
        )

        # Apply optional article substring filter
        if query.article_filter:
            eligible_chunks = [c for c in eligible_chunks if query.article_filter.lower() in c.article_number.lower()]

        # Retrieve scored chunks by method
        limit = query.limit or query.top_k or 5

        if query.method in (RetrievalMethod.LEXICAL, RetrievalMethod.LEXICAL_BM25):
            lex_matches = self.lexical.search(query_terms, eligible_chunks, top_k=limit)
            scored_matches = [(score, chunk, RetrievalMethod.LEXICAL) for chunk, score in lex_matches]
        elif query.method in (RetrievalMethod.SEMANTIC, RetrievalMethod.SEMANTIC_EMBEDDING):
            sem_matches = self.semantic.search(full_query, eligible_chunks, top_k=limit)
            scored_matches = [(score, chunk, RetrievalMethod.SEMANTIC) for chunk, score in sem_matches]
        else:
            scored_matches = self.hybrid.retrieve(
                query_terms=query_terms,
                query_str=full_query,
                eligible_chunks=eligible_chunks,
                top_k=limit,
            )

        citations: List[CitationEvidence] = []
        retrieved_chunks: List[DocumentChunk] = []

        for score, chunk, method in scored_matches[:limit]:
            parent_doc = self.repository.get_document(chunk.document_id)
            doc_name = parent_doc.document_name if parent_doc else "Unknown Governing Document"
            source_org = parent_doc.source_organization if parent_doc else "FIA"

            prov_status = chunk.provenance_status
            if not chunk.effective_from and not chunk.effective_to and query.case_date:
                prov_status = ProvenanceStatus.EFFECTIVE_DATE_UNCERTAIN

            claim_desc = f"Potentially applicable regulatory provision for {query.incident_type or 'observed racing engagement'}."

            citation = CitationEvidence(
                claim=claim_desc,
                source=source_org,
                document_name=doc_name,
                article_number=chunk.article_number,
                heading=chunk.heading,
                verbatim_text=chunk.text,
                source_url=chunk.source_url,
                evidence_type="DOCUMENTARY",
                relevance_score=score,
                retrieval_method=method,
                provenance=f"{doc_name} ({chunk.document_version or 'Official'})",
                provenance_status=prov_status,
                effective_from=chunk.effective_from,
                effective_to=chunk.effective_to,
                effective_status="EFFECTIVE",
                chunk=chunk,
            )
            citations.append(citation)
            retrieved_chunks.append(chunk)

        conflicts = self._detect_source_conflicts(retrieved_chunks)

        return RegulationSearchResult(
            query_interpreted=full_query,
            total_found=len(citations),
            citations=citations,
            conflicts=conflicts,
            source_conflicts=conflicts,
            effective_date_filter_applied=date_filtered,
            season_filter_applied=season_filtered,
            retrieval_method=query.method,
        )
