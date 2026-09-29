"""Evaluation framework for candidate incident detection against ground-truth reference cases.

CRITICAL PRINCIPLE:
    Reference cases are strictly evaluation fixtures.
    They are NEVER hardcoded into the detector or inserted into production incident tables.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel

from app.evidence.candidate import CandidateDossier


@dataclass
class ReferenceIncidentCase:
    """Ground-truth validation fixture representing an officially noted or penalized incident."""
    case_id: str
    session_id: str
    season: int
    round_name: str
    lap: int
    driver_a: str
    driver_b: str
    approx_time: str
    fia_document: str
    infringement_type: str
    official_finding: str
    description: str


# 2024 Italian Grand Prix (Monza) Official Reference Cases
MONZA_2024_REFERENCE_CASES: List[ReferenceIncidentCase] = [
    ReferenceIncidentCase(
        case_id="REF-MONZA-01",
        session_id="f1-2024-monza-race",
        season=2024,
        round_name="Monza",
        lap=1,
        driver_a="RIC",
        driver_b="HUL",
        approx_time="13:07:30",
        fia_document="FIA Document 54",
        infringement_type="Forcing Car Off Track",
        official_finding="Car 3 forced Car 27 off track approaching Turn 8 (Ascari). 5-second penalty imposed.",
        description="Ricciardo crowded Hulkenberg off the track on the opening lap.",
    ),
    ReferenceIncidentCase(
        case_id="REF-MONZA-02",
        session_id="f1-2024-monza-race",
        season=2024,
        round_name="Monza",
        lap=4,
        driver_a="HUL",
        driver_b="TSU",
        approx_time="13:11:00",
        fia_document="FIA Document 55",
        infringement_type="Causing a Collision",
        official_finding="Car 27 collided with Car 22 entering Turn 1. 10-second penalty imposed. Tsunoda retired.",
        description="Hulkenberg locked up into Turn 1 and collided with Tsunoda's sidepod.",
    ),
    ReferenceIncidentCase(
        case_id="REF-MONZA-03",
        session_id="f1-2024-monza-race",
        season=2024,
        round_name="Monza",
        lap=19,
        driver_a="MAG",
        driver_b="GAS",
        approx_time="13:30:15",
        fia_document="FIA Document 57",
        infringement_type="Causing a Collision",
        official_finding="Car 20 locked wheels and collided with Car 10 at Turn 4 (Variante della Roggia). 10-second penalty + 2 penalty points.",
        description="Magnussen attempted an inside pass at Turn 4, locked front axle and made contact with Gasly.",
    ),
]


class EvaluationMetrics(BaseModel):
    """Statistical verification metrics for candidate event detection."""
    total_candidates_detected: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    candidate_event_rate_per_hour: float
    evaluated_cases: List[Dict[str, str]]


def compute_temporal_overlap_seconds(
    start_a: str, end_a: str, start_b: str, end_b: str
) -> float:
    """Calculate temporal overlap duration in seconds between two time strings (HH:MM:SS)."""
    try:
        def to_sec(s: str) -> float:
            parts = s.split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])

        a0, a1 = to_sec(start_a), to_sec(end_a)
        b0, b1 = to_sec(start_b), to_sec(end_b)

        overlap_start = max(a0, b0)
        overlap_end = min(a1, b1)

        return max(0.0, overlap_end - overlap_start)
    except Exception:
        return 0.0


def evaluate_candidates_against_ground_truth(
    candidates: List[CandidateDossier],
    reference_cases: Optional[List[ReferenceIncidentCase]] = None,
    session_telemetry_hours: float = 1.4,
) -> EvaluationMetrics:
    """Compare candidate detections against official steward reference cases."""
    refs = reference_cases or MONZA_2024_REFERENCE_CASES

    matched_refs = set()
    matched_candidates = set()

    evaluated_details = []

    for ref in refs:
        found_match = False
        ref_drivers = {ref.driver_a.upper(), ref.driver_b.upper()}

        for cand in candidates:
            cand_drivers = {cand.driver_a.upper(), cand.driver_b.upper()}

            # Check driver pair match
            if ref_drivers == cand_drivers:
                # Check lap match or temporal proximity (within ~60 seconds)
                lap_match = (
                    cand.lap_number_a == ref.lap
                    or cand.lap_number_b == ref.lap
                )

                if lap_match:
                    found_match = True
                    matched_refs.add(ref.case_id)
                    matched_candidates.add(cand.candidate_id)
                    evaluated_details.append(
                        {
                            "case_id": ref.case_id,
                            "fia_document": ref.fia_document,
                            "match_status": "TRUE_POSITIVE",
                            "candidate_id": cand.candidate_id,
                            "candidate_peak": cand.event_peak,
                            "candidate_gap": f"{cand.minimum_gap_meters}m",
                            "candidate_closing": f"{cand.peak_closing_speed_ms}m/s",
                        }
                    )
                    break

        if not found_match:
            evaluated_details.append(
                {
                    "case_id": ref.case_id,
                    "fia_document": ref.fia_document,
                    "match_status": "FALSE_NEGATIVE",
                    "candidate_id": "NONE",
                    "candidate_peak": "N/A",
                    "candidate_gap": "N/A",
                    "candidate_closing": "N/A",
                }
            )

    tp = len(matched_refs)
    fn = len(refs) - tp
    fp = len(candidates) - len(matched_candidates)

    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1 = round((2.0 * precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0
    cand_rate = round(len(candidates) / session_telemetry_hours, 2) if session_telemetry_hours > 0 else 0.0

    return EvaluationMetrics(
        total_candidates_detected=len(candidates),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1_score=f1,
        candidate_event_rate_per_hour=cand_rate,
        evaluated_cases=evaluated_details,
    )
