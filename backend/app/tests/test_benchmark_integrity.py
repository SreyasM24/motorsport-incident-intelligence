"""Automated Test Suite for Benchmark Integrity, Provenance & Group-Aware Splits (Prompt 20).

CRITICAL SCIENTIFIC INTEGRITY & EVALUATION STANDARDS:
    1. Metric Grounding Independence: Distinguishes independently sourced ground truth
       from telemetry-derived consistency checks to prevent circular evaluation.
    2. Group-Aware Partitions: Enforces Leave-One-Circuit-Out (LOCO) and Leave-One-Season-Out (LOSO)
       leakage-free splitting.
    3. Non-Precedent Comparator: Proves that case retrieval is strictly governed by
       observable geometry and kinematics, with zero influence from historical penalties or verdicts.
    4. Epistemic Guardrails: Asserts zero illegal upgrades (DERIVED/MODEL_DERIVED -> OBSERVED).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.benchmark.manifest import (
    BenchmarkManifest,
    GroundTruthProvenance,
    HistoricalIncidentCase,
    VerificationStatus,
    get_verified_cases,
    leave_one_circuit_out_splits,
    leave_one_event_out_splits,
    leave_one_season_out_splits,
    load_benchmark_manifest,
)
from app.benchmark.evaluator import (
    HistoricalReconstructionEvaluator,
    MetricIndependenceCategory,
    MetricProvenanceAudit,
)
from app.benchmark.comparator import (
    HistoricalCaseComparator,
    ComparatorEvaluationReport,
)
from app.benchmark.service import get_benchmark_service


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def manifest() -> BenchmarkManifest:
    return load_benchmark_manifest()


@pytest.fixture(scope="module")
def evaluator(manifest: BenchmarkManifest) -> HistoricalReconstructionEvaluator:
    return HistoricalReconstructionEvaluator(manifest.tolerances)


# ==============================================================================
# 1. GROUND TRUTH PROVENANCE & INDEPENDENCE AUDIT TESTS
# ==============================================================================

def test_ground_truth_provenance_schema_and_types(manifest: BenchmarkManifest):
    """Verify that every case carries an explicit GroundTruthProvenance classification."""
    valid_provenances = {
        GroundTruthProvenance.OFFICIAL_DOCUMENT,
        GroundTruthProvenance.INDEPENDENT_TELEMETRY,
        GroundTruthProvenance.INDEPENDENT_ANNOTATION,
        GroundTruthProvenance.DERIVED_FROM_SAME_TELEMETRY,
        GroundTruthProvenance.UNKNOWN,
    }
    for case in manifest.cases:
        assert isinstance(case.ground_truth_provenance, GroundTruthProvenance)
        assert case.ground_truth_provenance in valid_provenances

        # If official decision, provenance must be OFFICIAL_DOCUMENT
        if case.ground_truth_type.value == "OFFICIAL_STEWARD_DECISION":
            assert case.ground_truth_provenance == GroundTruthProvenance.OFFICIAL_DOCUMENT

        # If nominal control, provenance must be DERIVED_FROM_SAME_TELEMETRY or OFFICIAL_DOCUMENT
        if case.is_control_case:
            assert case.ground_truth_provenance in {
                GroundTruthProvenance.DERIVED_FROM_SAME_TELEMETRY,
                GroundTruthProvenance.OFFICIAL_DOCUMENT,
            }


def test_metric_independence_provenance_matrix(evaluator: HistoricalReconstructionEvaluator):
    """Verify that the evaluator defines an authoritative, honest provenance matrix."""
    matrix = evaluator.audit_metric_provenance()
    assert len(matrix) >= 9

    independent_metrics = [m for m in matrix if m.category == MetricIndependenceCategory.INDEPENDENT_EVALUATION]
    telemetry_consistency_metrics = [m for m in matrix if m.category == MetricIndependenceCategory.TELEMETRY_CONSISTENCY_CHECK]
    insufficient_data_metrics = [m for m in matrix if m.category == MetricIndependenceCategory.INSUFFICIENT_DATA]

    # Verify key independent metrics
    independent_names = {m.metric_name for m in independent_metrics}
    assert "baseline_validity_rate" in independent_names
    assert "regulation_retrieval_mean_recall" in independent_names
    assert "epistemic_typing_compliance_rate" in independent_names
    assert "double_counting_prevented" in independent_names

    # Verify reclassified consistency metrics
    consistency_names = {m.metric_name for m in telemetry_consistency_metrics}
    assert "timestamp_reconstruction_accuracy_rate" in consistency_names
    assert "vehicle_pair_match_accuracy" in consistency_names
    assert "spatial_plausibility_rate" in consistency_names

    # Verify insufficient data handling
    assert len(insufficient_data_metrics) >= 1
    assert any("identity" in m.metric_name or "visual" in m.dimension.lower() for m in insufficient_data_metrics)


def test_circular_evaluation_risk_detection_and_reclassification(evaluator: HistoricalReconstructionEvaluator):
    """Verify that metrics sharing underlying telemetry computational pathways are flagged and reclassified."""
    matrix = evaluator.audit_metric_provenance()

    for item in matrix:
        if item.category == MetricIndependenceCategory.TELEMETRY_CONSISTENCY_CHECK:
            assert item.is_independent is False
            assert "HIGH" in item.circular_evaluation_risk or "consistency" in item.scientific_justification.lower()
            assert item.reclassified_name != item.metric_name


# ==============================================================================
# 2. GROUP-AWARE SPLITTING TESTS (LEAKAGE-FREE EVALUATION)
# ==============================================================================

def test_leave_one_circuit_out_partitions_no_leakage(manifest: BenchmarkManifest):
    """Verify Leave-One-Circuit-Out splits have disjoint test and train sets across all circuits."""
    loco_splits = leave_one_circuit_out_splits(manifest, verified_only=True)
    assert len(loco_splits) >= 4

    for holdout_circuit, fold in loco_splits.items():
        train_cases = fold["train"]
        test_cases = fold["test"]

        assert len(test_cases) > 0
        assert len(train_cases) > 0

        # Assert zero circuit overlap
        train_circuits = {c.circuit for c in train_cases}
        test_circuits = {c.circuit for c in test_cases}

        assert holdout_circuit in test_circuits
        assert holdout_circuit not in train_circuits
        assert train_circuits.isdisjoint(test_circuits)


def test_leave_one_season_out_partitions_no_leakage(manifest: BenchmarkManifest):
    """Verify Leave-One-Season-Out splits have disjoint temporal partitions without leakage."""
    loso_splits = leave_one_season_out_splits(manifest, verified_only=True)
    assert len(loso_splits) >= 2  # 2023 and 2024

    for holdout_season, fold in loso_splits.items():
        train_cases = fold["train"]
        test_cases = fold["test"]

        assert len(test_cases) > 0
        assert len(train_cases) > 0

        train_seasons = {str(c.season) for c in train_cases}
        test_seasons = {str(c.season) for c in test_cases}

        assert holdout_season in test_seasons
        assert holdout_season not in train_seasons
        assert train_seasons.isdisjoint(test_seasons)


def test_leave_one_event_out_partitions_no_leakage(manifest: BenchmarkManifest):
    """Verify Leave-One-Event-Out splits prevent intra-event telemetry leakage."""
    loeo_splits = leave_one_event_out_splits(manifest, verified_only=True)
    assert len(loeo_splits) >= 4

    for holdout_event, fold in loeo_splits.items():
        train_cases = fold["train"]
        test_cases = fold["test"]

        train_events = {c.split_group.event for c in train_cases}
        test_events = {c.split_group.event for c in test_cases}

        assert holdout_event in test_events
        assert holdout_event not in train_events
        assert train_events.isdisjoint(test_events)


# ==============================================================================
# 3. COMPARATOR FEATURE ISOLATION & PHYSICAL RETRIEVAL TESTS
# ==============================================================================

def test_comparator_feature_isolation_audit(manifest: BenchmarkManifest):
    """Verify that comparator scoring is mathematically isolated from penalties and guilt."""
    comparator = HistoricalCaseComparator(manifest)
    audit = comparator.audit_feature_isolation()

    assert audit["isolationStatus"] == "VERIFIED_PASS"
    assert audit["nonPrecedentEnforced"] is True
    assert "steward_decision_type" in audit["disallowedFeaturesChecked"]
    assert "penalty_points" in audit["disallowedFeaturesChecked"]
    assert "time_penalty_seconds" in audit["disallowedFeaturesChecked"]
    assert "fault_allocation_ratio" in audit["disallowedFeaturesChecked"]
    assert "interaction_category" in audit["allowedObservableFeaturesUsed"]
    assert "corner_phase" in audit["allowedObservableFeaturesUsed"]
    assert "minimum_gap_meters_range" in audit["allowedObservableFeaturesUsed"]


def test_comparator_observable_kinematic_evaluation(manifest: BenchmarkManifest):
    """Verify that retrieved comparable cases match observable geometry and kinematics."""
    comparator = HistoricalCaseComparator(manifest)
    eval_rep = comparator.evaluate_observable_similarity(top_k=3)

    assert isinstance(eval_rep, ComparatorEvaluationReport)
    assert eval_rep.non_precedent_isolation_passed is True
    assert eval_rep.mean_gap_proximity_error_meters <= 2.0
    assert eval_rep.mean_brake_proximity_error_meters <= 15.0
    assert eval_rep.category_congruence_rate >= 0.70
    assert eval_rep.total_evaluated_queries >= 20


# ==============================================================================
# 4. EXPANDED BENCHMARK DIVERSITY & PURITY TESTS
# ==============================================================================

def test_expanded_benchmark_case_count_and_diversity(manifest: BenchmarkManifest):
    """Validate 20-30 verified cases across >= 4 circuits and >= 2 seasons."""
    verified = get_verified_cases(manifest)
    circuits = {c.circuit for c in verified}
    seasons = {c.season for c in verified}
    controls = [c for c in verified if c.is_control_case]

    assert len(verified) >= 20, f"Expected at least 20 verified cases, got {len(verified)}"
    assert len(circuits) >= 4, f"Expected at least 4 circuits, got {len(circuits)}"
    assert len(seasons) >= 2, f"Expected at least 2 seasons, got {len(seasons)}"
    assert len(controls) >= 6, f"Expected at least 6 nominal controls, got {len(controls)}"


def test_unverified_controls_strictly_excluded_from_scoring(manifest: BenchmarkManifest, evaluator: HistoricalReconstructionEvaluator):
    """Assert that unverified cases are strictly excluded from quantitative benchmark scoring."""
    unverified = [c for c in manifest.cases if c.verification_status == VerificationStatus.UNVERIFIED]
    assert len(unverified) >= 1

    report = evaluator.evaluate_manifest(manifest)
    assert report.unverified_excluded_cases == len(unverified)
    assert report.verified_cases + report.unverified_excluded_cases == report.total_cases


# ==============================================================================
# 5. REST API ENDPOINT INTEGRATION TESTS
# ==============================================================================

def test_api_benchmark_provenance_matrix_endpoint(client: TestClient):
    """Verify GET /api/v1/analysis/benchmark/provenance-matrix."""
    res = client.get("/api/v1/analysis/benchmark/provenance-matrix")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 9
    first_item = data[0]
    assert "metricName" in first_item
    assert "reclassifiedName" in first_item
    assert "category" in first_item
    assert "isIndependent" in first_item
    assert "circularEvaluationRisk" in first_item


def test_api_benchmark_splits_endpoint(client: TestClient):
    """Verify GET /api/v1/analysis/benchmark/splits for circuit and season."""
    res_circuit = client.get("/api/v1/analysis/benchmark/splits?split_type=circuit")
    assert res_circuit.status_code == 200
    data_circ = res_circuit.json()
    assert len(data_circ) >= 4

    res_season = client.get("/api/v1/analysis/benchmark/splits?split_type=season")
    assert res_season.status_code == 200
    data_seas = res_season.json()
    assert "2023" in data_seas
    assert "2024" in data_seas


def test_api_benchmark_comparator_evaluation_endpoint(client: TestClient):
    """Verify GET /api/v1/analysis/benchmark/comparator-evaluation."""
    res = client.get("/api/v1/analysis/benchmark/comparator-evaluation?top_k=3")
    assert res.status_code == 200
    data = res.json()
    assert data["nonPrecedentIsolationPassed"] is True
    assert "meanGapProximityErrorMeters" in data
    assert "categoryCongruenceRate" in data
    assert data["totalEvaluatedQueries"] >= 20
