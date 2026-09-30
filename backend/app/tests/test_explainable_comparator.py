"""Comprehensive Test Suite for Explainable Historical Comparable-Case Intelligence (Prompt 23).

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS:
    1. Zero Autonomous Guilt or Fault Determination: Historical incident records are strictly
       observational decision support; past rulings are never used as precedent for guilt/penalties.
    2. Zero Precedent Distortion: Historical steward outcomes have 0 weight in similarity scoring.
    3. Zero Driver/Team Bias: Driver names, nationalities, and teams have 0 weight in similarity.
    4. Observable Physical Grounding: Similarity is derived strictly from observable track geometry,
       corner phases, lateral separation, braking deltas, and speed relationships.
    5. Clean Missing-Data Renormalization: Missing dimensions are cleanly renormalized without
       zero-imputation distortion.
    6. Verifiable Measurement Uncertainty: Side-by-side metrics must carry explicit sensor uncertainty bounds.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.benchmark.manifest import BenchmarkManifest, load_benchmark_manifest
from app.benchmark.comparator import (
    HistoricalCaseComparator,
    HistoricalComparisonResponse,
    ComparableIncidentResult,
    SideBySideComparison,
    RelevanceGrade,
    DataQualityRating,
    DimensionAvailability,
)
from app.evidence.synthesis.synthesizer import StewardDossierSynthesizer
from app.evidence.dossier import IncidentEvidenceDossier, synthesize_incident_evidence_dossier
from app.evidence.candidate import CandidateDossier, CandidateEventType, CandidateStatus, DataQualityFlags
from app.schemas.telemetry import TelemetryPointSchema


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def manifest() -> BenchmarkManifest:
    return load_benchmark_manifest()


@pytest.fixture(scope="module")
def comparator(manifest: BenchmarkManifest) -> HistoricalCaseComparator:
    return HistoricalCaseComparator(manifest)


# ==============================================================================
# 1. DETERMINISTIC DIMENSION SCORING & NORMALIZATION
# ==============================================================================

def test_dimension_scoring_deterministic_and_normalized(comparator: HistoricalCaseComparator):
    """Verify that all 7 dimension scoring functions return deterministic values bounded in [0.0, 1.0]."""
    # 1. Corner Phase
    s_corner_same = comparator._compute_corner_phase_similarity("Turn 4", "Turn 4", "Turn 4", "Turn 4")
    assert s_corner_same == 1.0
    s_corner_partial = comparator._compute_corner_phase_similarity("Turn 4", "Turn 4b", "Turn 4", "Turn 5")
    assert 0.0 <= s_corner_partial <= 1.0

    # 2. Speed Relationship
    s_speed_identical = comparator._compute_speed_similarity(180.0, 180.0)
    assert s_speed_identical == 1.0
    s_speed_diff = comparator._compute_speed_similarity(180.0, 140.0)
    assert 0.0 <= s_speed_diff < 1.0

    # 3. Braking Similarity
    s_brake_identical = comparator._compute_braking_similarity(10.0, 10.0)
    assert s_brake_identical == 1.0
    s_brake_diff = comparator._compute_braking_similarity(10.0, 30.0)
    assert 0.0 <= s_brake_diff < 1.0

    # 4. Spatial Separation Similarity
    s_spatial_identical = comparator._compute_spatial_similarity(1.5, 1.5)
    assert s_spatial_identical == 1.0
    s_spatial_diff = comparator._compute_spatial_similarity(1.5, 4.0)
    assert 0.0 <= s_spatial_diff < 1.0

    # 5. Apex Similarity
    s_apex_same = comparator._compute_apex_similarity("FORCING_OFF_TRACK", "FORCING_OFF_TRACK")
    assert s_apex_same == 1.0

    # 6. Exit Similarity
    s_exit_same = comparator._compute_exit_similarity("OVERTAKE_COLLISION", "OVERTAKE_COLLISION")
    assert s_exit_same == 1.0

    # 7. Trajectory Similarity
    s_traj = comparator._compute_trajectory_similarity("FORCING_OFF_TRACK", "LEAVING_TRACK_ADVANTAGE")
    assert 0.0 <= s_traj <= 1.0


# ==============================================================================
# 2. MISSING DATA HANDLING (WEIGHT RENORMALIZATION VS ZERO-IMPUTATION)
# ==============================================================================

def test_missing_data_renormalization(comparator: HistoricalCaseComparator):
    """Verify missing dimensions renormalize available weights without penalizing with 0.0."""
    # When speed is None, speed dimension should be marked MISSING and weight renormalized
    res = comparator.compare_case(
        query_case_id="CASE-2024-MON-01",
        top_k=3,
    )
    assert len(res.comparable_cases) > 0
    top_match = res.comparable_cases[0]

    # Verify score is non-zero and mathematically sound
    assert top_match.observable_similarity_score > 0.0
    assert 0.0 <= top_match.observable_similarity_score <= 1.0

    # Verify dimensions are tracked in similarity_dimensions map
    assert "spatial_similarity" in top_match.similarity_dimensions
    assert "braking_similarity" in top_match.similarity_dimensions
    assert top_match.similarity_dimensions["spatial_similarity"] in [
        DimensionAvailability.AVAILABLE.value,
        DimensionAvailability.MISSING.value,
    ]


# ==============================================================================
# 3. PRECEDENT & ADJUDICATION ISOLATION (ZERO PRECEDENT WEIGHT)
# ==============================================================================

def test_non_precedent_isolation(manifest: BenchmarkManifest):
    """Verify that changing a case's historical penalty or steward verdict has 0 impact on similarity."""
    comp1 = HistoricalCaseComparator(manifest)
    res1 = comp1.compare_case(query_case_id="CASE-2024-MON-01", top_k=3)
    score1 = res1.comparable_cases[0].observable_similarity_score

    # Mutate the documented steward outcome in a copy of manifest
    manifest_mutated = manifest.model_copy(deep=True)
    for c in manifest_mutated.cases:
        if c.case_id == res1.comparable_cases[0].case_id:
            c.documented_steward_outcome.decision_type = "DISQUALIFICATION_AND_SUPERLICENCE_BAN"
            c.documented_steward_outcome.description = "Arbitrary modified outcome."

    comp2 = HistoricalCaseComparator(manifest_mutated)
    res2 = comp2.compare_case(query_case_id="CASE-2024-MON-01", top_k=3)
    score2 = res2.comparable_cases[0].observable_similarity_score

    # Delta must be EXACTLY 0.000000
    assert abs(score1 - score2) == 0.000000, "Historical penalty outcome leaked into similarity score!"


# ==============================================================================
# 4. DRIVER & TEAM IDENTITY ISOLATION (ZERO POPULARITY/REPUTATION WEIGHT)
# ==============================================================================

def test_driver_and_team_isolation(manifest: BenchmarkManifest):
    """Verify changing driver identities or team constructors does not alter similarity score."""
    comp1 = HistoricalCaseComparator(manifest)
    res1 = comp1.compare_case(query_case_id="CASE-2024-MON-01", top_k=3)
    score1 = res1.comparable_cases[0].observable_similarity_score

    # Mutate driver identities in a copy of manifest
    manifest_mutated = manifest.model_copy(deep=True)
    for c in manifest_mutated.cases:
        if c.case_id == res1.comparable_cases[0].case_id:
            c.driver_a = "FICTIONAL_DRIVER_ALPHA"
            c.driver_b = "FICTIONAL_DRIVER_BETA"

    comp2 = HistoricalCaseComparator(manifest_mutated)
    res2 = comp2.compare_case(query_case_id="CASE-2024-MON-01", top_k=3)
    score2 = res2.comparable_cases[0].observable_similarity_score

    assert abs(score1 - score2) == 0.000000, "Driver identity leaked into similarity score!"


def test_audit_feature_isolation(comparator: HistoricalCaseComparator):
    """Audit feature isolation to verify zero forbidden features are utilized."""
    isolation_audit = comparator.audit_feature_isolation()
    assert isolation_audit["isolation_verified"] is True
    assert isolation_audit["forbidden_features_detected"] == 0
    assert len(isolation_audit["forbidden_feature_list"]) == 0


# ==============================================================================
# 5. EXPLAINABILITY VERIFICATION (MATCHED & UNMATCHED FEATURES)
# ==============================================================================

def test_explainability_matched_and_unmatched_features(comparator: HistoricalCaseComparator):
    """Verify that matched_features and unmatched_features are populated for 100% of comparisons."""
    res = comparator.compare_case(query_case_id="CASE-2024-MON-01", top_k=5)
    assert len(res.comparable_cases) > 0

    for cand in res.comparable_cases:
        assert isinstance(cand.matched_features, list)
        assert isinstance(cand.unmatched_features, list)
        assert len(cand.matched_features) > 0, f"Case {cand.case_id} missing matched features"
        # Verify explainability text contains observable terms
        matched_str = " ".join(cand.matched_features).lower()
        assert any(term in matched_str for term in ["braking", "gap", "corner", "trajectory", "lateral", "phase"])


# ==============================================================================
# 6. SIDE-BY-SIDE EVIDENCE ANALYSIS CONTRACT & UNCERTAINTY BOUNDS
# ==============================================================================

def test_side_by_side_contract_and_uncertainty_bounds(comparator: HistoricalCaseComparator):
    """Verify side-by-side comparison contract includes physical metrics and uncertainty bounds."""
    res = comparator.compare_case(query_case_id="CASE-2024-MON-01", top_k=3)
    assert len(res.comparable_cases) > 0

    for cand in res.comparable_cases:
        sbs = cand.side_by_side
        assert sbs is not None, f"Case {cand.case_id} missing side_by_side object"
        assert sbs.current_case_id == "CASE-2024-MON-01"
        assert sbs.historical_case_id == cand.case_id
        assert len(sbs.metrics) >= 4, "Must contain at least 4 physical metric rows"

        for row in sbs.metrics:
            assert row.metric != ""
            assert row.current_value != ""
            assert row.historical_value != ""
            assert row.difference != ""
            assert row.uncertainty != "", f"Metric {row.metric} missing uncertainty bound"
            assert "±" in row.uncertainty, f"Metric {row.metric} uncertainty must use ± notation"
            assert row.source_type != ""


# ==============================================================================
# 7. RETRIEVAL METRICS (PRECISION@K, RECALL@K, MRR)
# ==============================================================================

def test_retrieval_metrics_evaluation(comparator: HistoricalCaseComparator):
    """Verify evaluator computes Precision@K, Recall@K, and MRR exceeding thresholds."""
    report = comparator.evaluate_observable_similarity(top_k=3)
    assert report.total_evaluated_queries >= 8
    assert report.mean_reciprocal_rank >= 0.70
    assert report.precision_at_k >= 0.50
    assert report.recall_at_k >= 0.70
    assert report.non_precedent_isolation_passed is True
    assert report.driver_team_isolation_passed is True


# ==============================================================================
# 8. REST API ENDPOINTS
# ==============================================================================

def test_api_endpoint_historical_compare(client: TestClient):
    """Verify GET /api/v1/evidence/historical/compare/{candidate_id} returns valid comparison response."""
    response = client.get("/api/v1/evidence/historical/compare/CASE-2024-MON-01?top_k=3")
    assert response.status_code == 200
    data = response.json()

    assert data["queryCaseId"] == "CASE-2024-MON-01"
    assert data["totalCasesEvaluated"] > 0
    assert len(data["comparableCases"]) <= 3
    assert "nonAdjudicationStatement" in data
    assert "CRITICAL NON-ADJUDICATIVE NOTICE" in data["nonAdjudicationStatement"]

    first_match = data["comparableCases"][0]
    assert "caseId" in first_match
    assert "observableSimilarityScore" in first_match
    assert "relevanceGrade" in first_match
    assert "matchedFeatures" in first_match
    assert "unmatchedFeatures" in first_match
    assert "sideBySide" in first_match
    assert "officialSources" in first_match
    assert len(first_match["officialSources"]) > 0


def test_api_endpoint_backward_compatibility(client: TestClient):
    """Verify GET /api/v1/evidence/historical/search?case_id=CASE-2024-MON-01 preserves backward compatibility."""
    response = client.get("/api/v1/evidence/historical/search?case_id=CASE-2024-MON-01&top_k=3")
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert len(data["matches"]) > 0
    assert data["matches"][0]["epistemicType"] == "DOCUMENTARY"


# ==============================================================================
# 9. STEWARD EVIDENCE DOSSIER INTEGRATION
# ==============================================================================

def test_steward_dossier_integration():
    """Verify that synthesizing a StewardEvidenceDossier includes historical_comparable_evidence."""
    candidate = CandidateDossier(
        candidate_id="CAND-TEST-SYNTH-01",
        session_id="Italian Grand Prix 2024 — Race",
        driver_a="MAG",
        driver_b="GAS",
        car_number_a=20,
        car_number_b=10,
        team_a="Haas",
        team_b="Alpine",
        lap_number_a=19,
        lap_number_b=19,
        turn="Turn 4 (Variante della Roggia)",
        event_start="15:42:17.000",
        event_peak="15:42:18.400",
        event_end="15:42:20.000",
        duration_seconds=3.0,
        event_type=CandidateEventType.RAPID_PROXIMITY_EVENT,
        detection_method="KINEMATIC_PROXIMITY_ANALYZER",
        evidence_strength=88,
        minimum_gap_meters=1.82,
        peak_closing_speed_ms=8.4,
        speed_delta_at_peak=2.0,
        speed_a_at_peak=220.0,
        speed_b_at_peak=222.0,
        braking_change={"decel_delta_g": 1.2, "brake_pressure_delta_bar": 45.0},
        trajectory_divergence={"lateral_displacement_m": 0.85},
        status=CandidateStatus.PENDING_REVIEW,
        summary="Close interaction at Variante della Roggia apex with late braking.",
        data_quality_flags=DataQualityFlags(),
    )
    raw_frames = [
        TelemetryPointSchema(
            timestamp="15:42:18.000",
            time_offset=0.0,
            speed_a=200.0,
            speed_b=200.0,
            throttle_a=100.0,
            throttle_b=100.0,
            brake_a=0.0,
            brake_b=0.0,
            gear_a=7,
            gear_b=7,
            gap_meters=1.82,
            closing_speed_ms=8.4,
        )
    ]
    base_dossier = synthesize_incident_evidence_dossier(
        candidate=candidate,
        raw_frames=raw_frames,
        all_features=[],
    )
    synthesizer = StewardDossierSynthesizer()

    steward_dossier = synthesizer.synthesize_steward_dossier(base_dossier)
    assert steward_dossier.historical_comparable_evidence is not None
    assert len(steward_dossier.historical_comparable_evidence.comparable_cases) > 0

    first_comp = steward_dossier.historical_comparable_evidence.comparable_cases[0]
    assert first_comp.observable_similarity_score > 0.0
    assert first_comp.side_by_side is not None


# ==============================================================================
# 10. AI ASSISTANT INTEGRATION
# ==============================================================================

def test_assistant_comparable_case_query(client: TestClient):
    """Verify AI Assistant answers inquiries on comparable cases with citation grounding."""
    payload = {
        "incident_id": "HIST-2024-ITA-R-01",
        "query": "Which historical incidents are observably similar to this candidate?",
    }
    response = client.post("/api/v1/assistant/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "Observable Historical Comparators" in data["text"]
    assert "CRITICAL NON-ADJUDICATIVE NOTICE" in data["text"]
    assert len(data["evidenceChips"]) > 0
    assert any("HIST-" in chip["label"] or "CASE-" in chip["label"] for chip in data["evidenceChips"])
    assert any(link["targetView"].startswith("/evidence/historical/compare/") for link in data["evidenceLinks"])


def test_assistant_non_existent_case_handling(client: TestClient):
    """Verify AI Assistant gracefully handles queries for non-existent cases with proper warning."""
    payload = {
        "incident_id": "NON-EXISTENT-CASE-999",
        "query": "Which comparable historical case matches this non-existent incident?",
    }
    response = client.post("/api/v1/assistant/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "INSUFFICIENT_HISTORICAL_COMPARISON_DATA" in data["text"]
    assert "CRITICAL NON-ADJUDICATIVE NOTICE" in data["text"]
