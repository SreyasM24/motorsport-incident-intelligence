"""Historical Incident Retriever — Citation-Grounded Benchmark & Comparator Integration.

Provides documentary search over verified historical incident cases and connects
observable geometric similarity while strictly isolating historical steward outcomes
from being used as binding precedent or autonomous penalty recommendations.
"""

from typing import Any, Dict, List, Optional
import re

from app.benchmark.manifest import BenchmarkManifest, load_benchmark_manifest
from app.benchmark.comparator import HistoricalCaseComparator
from app.knowledge.models import (
    HistoricalEvidenceResult,
    HistoricalSearchResult,
    ProvenanceStatus,
)


class HistoricalIncidentKnowledgeRetriever:
    """Retrieves verified historical incident comparators with strict non-adjudication isolation."""

    NON_ADJUDICATIVE_STATEMENT: str = (
        "CRITICAL NON-ADJUDICATIVE NOTICE: Historical incident records and steward outcomes "
        "are preserved strictly as documentary reference material. Prior adjudications do NOT "
        "constitute binding legal precedent, automated fault assignments, or penalty recommendations."
    )

    def __init__(self, manifest: Optional[BenchmarkManifest] = None):
        self.manifest = manifest or load_benchmark_manifest()
        self.comparator = HistoricalCaseComparator(self.manifest)

    def retrieve_by_case_id(
        self,
        case_id: str,
        top_k: int = 3,
    ) -> HistoricalSearchResult:
        """Retrieve empirically comparable historical cases based on observable kinematics."""
        raw_matches = self.comparator.find_comparable_incidents(
            query_case_id=case_id,
            top_k=top_k,
        )

        matches: List[HistoricalEvidenceResult] = []
        for m in raw_matches:
            matches.append(
                HistoricalEvidenceResult(
                    case_id=m.case_id,
                    season=m.season,
                    event=m.event,
                    circuit=m.circuit,
                    corner=m.corner,
                    interaction_category=m.interaction_category,
                    observable_similarity_score=m.observable_similarity_score,
                    observable_physical_dimensions=m.physical_dimensions,
                    documentary_reference={
                        "official_document": m.documentary_context.official_document,
                        "document_identifier": m.documentary_context.document_identifier,
                        "documented_decision_type": m.documentary_context.decision_type,
                        "documented_decision_summary": m.documentary_context.decision_summary,
                        "epistemic_status": m.documentary_context.epistemic_status,
                    },
                    epistemic_notice=self.NON_ADJUDICATIVE_STATEMENT,
                    provenance_status=ProvenanceStatus.CANONICAL_DOCUMENTED,
                    epistemic_type="DOCUMENTARY",
                )
            )

        return HistoricalSearchResult(
            query_case_id=case_id,
            total_comparators_considered=len(self.manifest.cases),
            matches=matches,
            non_adjudication_statement=self.NON_ADJUDICATIVE_STATEMENT,
        )

    def search_historical_cases(
        self,
        query: str,
        season: Optional[int] = None,
        circuit: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> HistoricalSearchResult:
        """Search historical incident records using observable text queries and optional filters."""
        q_tokens = set(re.findall(r"\w+", query.lower())) if query else set()

        scored_cases = []
        for case in self.manifest.cases:
            if season is not None and case.season != season:
                continue
            if circuit and circuit.lower() not in case.circuit.lower():
                continue
            if category and category.upper() not in case.interaction_category.value.upper():
                continue

            # Compute lexical similarity against observable descriptive text
            # (circuit, corner, interaction_category, description, drivers)
            text_corpus = (
                f"{case.circuit} {case.corner} {case.interaction_category.value} "
                f"{case.documented_incident_description} {case.driver_a} {case.driver_b}"
            ).lower()

            corpus_tokens = set(re.findall(r"\w+", text_corpus))
            overlap = len(q_tokens.intersection(corpus_tokens))
            score = round(overlap / max(1, len(q_tokens)), 3) if q_tokens else 0.5

            scored_cases.append((score, case))

        # Sort by similarity score descending
        scored_cases.sort(key=lambda x: x[0], reverse=True)

        matches: List[HistoricalEvidenceResult] = []
        for score, c in scored_cases[:top_k]:
            matches.append(
                HistoricalEvidenceResult(
                    case_id=c.case_id,
                    season=c.season,
                    event=c.event,
                    circuit=c.circuit,
                    corner=c.corner,
                    interaction_category=c.interaction_category.value,
                    observable_similarity_score=score,
                    observable_physical_dimensions={
                        "minimum_gap_meters_range": c.expected_reconstruction_targets.minimum_gap_meters_range,
                        "delta_brake_meters_range": c.expected_reconstruction_targets.delta_brake_meters_range,
                        "primary_turn": c.expected_reconstruction_targets.primary_turn,
                    },
                    documentary_reference={
                        "official_document": c.official_document,
                        "document_identifier": c.document_identifier,
                        "documented_decision_type": c.documented_steward_outcome.decision_type,
                        "documented_decision_summary": c.documented_steward_outcome.description,
                        "epistemic_status": "DOCUMENTARY",
                    },
                    epistemic_notice=self.NON_ADJUDICATIVE_STATEMENT,
                    provenance_status=ProvenanceStatus.CANONICAL_DOCUMENTED,
                    epistemic_type="DOCUMENTARY",
                )
            )

        return HistoricalSearchResult(
            query_description=query,
            total_comparators_considered=len(self.manifest.cases),
            matches=matches,
            non_adjudication_statement=self.NON_ADJUDICATIVE_STATEMENT,
        )
