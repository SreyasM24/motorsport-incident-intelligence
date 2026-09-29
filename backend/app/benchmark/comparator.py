"""Historical Incident Comparator — Observable Geometric Similarity (Prompt 19).

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS:
    1. Zero Penalty Recommender: Does NOT recommend penalties or infer driver guilt
       from past steward rulings.
    2. Observable Physical Dimensions: Case similarity is computed strictly over
       observable track geometry, speed profiles, braking deltas, and lateral clearance.
    3. Separate Documentary Context: Historical steward decisions are displayed strictly
       as isolated documentary references, never as binding precedent or automated verdicts.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.benchmark.manifest import BenchmarkManifest, HistoricalIncidentCase


class HistoricalDocumentaryContext(BaseModel):
    """Documentary context model with automatic camelCase serialization."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    official_document: str
    document_identifier: str
    decision_type: str
    decision_summary: str
    epistemic_status: str = "DOCUMENTARY"


class ComparableIncidentMatch(BaseModel):
    """An empirical historical case match based purely on observable physical dimensions."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    case_id: str
    event: str
    season: int
    circuit: str
    corner: str
    interaction_category: str
    observable_similarity_score: float
    physical_dimensions: Dict[str, Any]
    documentary_context: HistoricalDocumentaryContext
    epistemic_warning: str = Field(
        default="CRITICAL NON-ADJUDICATIVE NOTICE: Historical steward rulings are documentary records only. Prior outcomes do NOT determine current guilt or penalty recommendations.",
    )


class HistoricalCaseComparator:
    """Finds empirically comparable historical incidents without predicting penalties."""

    def __init__(self, manifest: BenchmarkManifest):
        self.manifest = manifest

    def find_comparable_incidents(
        self,
        query_case_id: Optional[str] = None,
        query_features: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> List[ComparableIncidentMatch]:
        """Find comparable cases based on observable kinematics and track geometry."""
        target_case: Optional[HistoricalIncidentCase] = None
        if query_case_id:
            for c in self.manifest.cases:
                if c.case_id == query_case_id:
                    target_case = c
                    break

        # Fallback or external feature query
        feats = query_features or {}
        if target_case:
            cat = target_case.interaction_category.value
            corner = target_case.corner
            expected_gap = sum(target_case.expected_reconstruction_targets.minimum_gap_meters_range) / 2.0
            expected_db = sum(target_case.expected_reconstruction_targets.delta_brake_meters_range) / 2.0
        else:
            cat = feats.get("category", "FORCING_OFF_TRACK")
            corner = feats.get("corner", "Turn 4")
            expected_gap = feats.get("gap_meters", 1.5)
            expected_db = feats.get("delta_brake", 10.0)

        matches: List[Tuple[float, HistoricalIncidentCase]] = []

        for candidate in self.manifest.cases:
            if query_case_id and candidate.case_id == query_case_id:
                continue

            score = 0.0

            # 1. Category similarity (observable interaction type)
            if candidate.interaction_category.value == cat:
                score += 0.40

            # 2. Track / Corner Phase similarity
            if candidate.corner.split()[0] in corner:
                score += 0.20

            # 3. Gap proximity similarity
            cand_gap = sum(candidate.expected_reconstruction_targets.minimum_gap_meters_range) / 2.0
            gap_diff = abs(expected_gap - cand_gap)
            gap_score = max(0.0, 0.20 - (gap_diff * 0.05))
            score += gap_score

            # 4. Braking delta similarity
            cand_db = sum(candidate.expected_reconstruction_targets.delta_brake_meters_range) / 2.0
            db_diff = abs(expected_db - cand_db)
            db_score = max(0.0, 0.20 - (db_diff * 0.01))
            score += db_score

            matches.append((round(score, 3), candidate))

        matches.sort(key=lambda x: x[0], reverse=True)
        results: List[ComparableIncidentMatch] = []

        for sim_score, case in matches[:top_k]:
            results.append(
                ComparableIncidentMatch(
                    case_id=case.case_id,
                    event=case.event,
                    season=case.season,
                    circuit=case.circuit,
                    corner=case.corner,
                    interaction_category=case.interaction_category.value,
                    observable_similarity_score=sim_score,
                    physical_dimensions={
                        "minimum_gap_meters_range": case.expected_reconstruction_targets.minimum_gap_meters_range,
                        "delta_brake_meters_range": case.expected_reconstruction_targets.delta_brake_meters_range,
                        "primary_turn": case.expected_reconstruction_targets.primary_turn,
                    },
                    documentary_context=HistoricalDocumentaryContext(
                        official_document=case.official_document,
                        document_identifier=case.document_identifier,
                        decision_type=case.documented_steward_outcome.decision_type,
                        decision_summary=case.documented_steward_outcome.description,
                        epistemic_status="DOCUMENTARY",
                    ),
                )
            )

        return results
