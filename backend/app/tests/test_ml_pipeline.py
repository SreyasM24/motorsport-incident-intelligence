"""Comprehensive test suite for ML Readiness, Evaluation Framework & FIA Provenance Audit (Prompt 10).

Covers:
1. Feature extraction determinism, vectorization, and missing sensor imputation
2. Leakage prevention: exclusion of identifiers and group-level partitioning
3. Model fitting, calibration bounds (0 <= p <= 1), and uncertainty intervals
4. Directional feature contributions and steward explainability
5. Structured MLEvidence schema contract and dossier integration
6. Benchmark evaluation against Deterministic Candidate Detector (Prompt 05/06)
7. REST API endpoints (/ml-evaluation, /benchmark-evaluation, /frontend-incident)
8. FIA Provenance audit: statutory 2.00m regulation vs 5.63m engineering reference
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.ml.dataset import (
    MLDataset,
    MLSample,
    LabelProvenance,
    build_canonical_dataset,
    build_canonical_monza_dataset,
)
from app.ml.evaluation import BenchmarkEvaluationReport
from app.ml.features import (
    FEATURE_NAMES_V1,
    FEATURE_NAMES_V1_1,
    FEATURE_VERSION,
    extract_features_from_dict,
    vectorize_features,
)
from app.ml.models import (
    CandidateInteractionClassifier,
    CandidateRandomForestClassifier,
    CandidateXGBoostClassifier,
    get_candidate_classifier,
)
from app.schemas.ml_evidence import MLEvidence
from app.schemas.overtake_geometry import (
    ExitClearanceMetrics,
    FIAGuidelineReference,
    MeasurementConfidence,
)


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. FEATURE EXTRACTION & GUARDRAILS TESTS
# ==============================================================================

def test_feature_names_exclude_identifiers():
    """Verify strictly NO driver identities, candidate IDs, teams, or timestamps in features."""
    forbidden_terms = ["driver", "candidate_id", "session_id", "team", "turn", "timestamp", "guilt", "fault", "penalty"]
    for feat in FEATURE_NAMES_V1:
        for term in forbidden_terms:
            assert term not in feat.lower(), f"Forbidden identifier or fault token '{term}' found in feature '{feat}'"


def test_feature_extraction_deterministic_and_imputed():
    """Verify feature extractor handles incomplete dictionaries and maps missing values to defaults."""
    incomplete_dict = {
        "min_gap_m": 1.15,
        "peak_closing_speed_ms": 6.80,
    }
    # Test v1 backwards compatibility
    feats_v1 = extract_features_from_dict(incomplete_dict, feature_schema=FEATURE_NAMES_V1)
    assert len(feats_v1) == len(FEATURE_NAMES_V1)
    vec_v1 = vectorize_features(feats_v1, feature_schema=FEATURE_NAMES_V1)
    assert vec_v1.shape == (len(FEATURE_NAMES_V1),)

    # Test v1.1 active canonical schema with missingness indicators
    feats = extract_features_from_dict(incomplete_dict)
    assert len(feats) == len(FEATURE_NAMES_V1_1)
    assert feats["min_gap_m"] == 1.15
    assert feats["peak_closing_speed_ms"] == 6.80
    assert feats["sync_flag"] == 1.0  # default
    assert feats["missing_telemetry_flag"] == 0.0  # default
    # Verify unobserved sensor indicators were set to 1.0 (unobserved)
    assert feats["missing_brake_flag"] == 1.0
    assert feats["missing_baseline_flag"] == 1.0

    # Verify vectorization produces correct 1D array
    vec = vectorize_features(feats)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (len(FEATURE_NAMES_V1_1),)
    assert not np.isnan(vec).any()
    assert not np.isinf(vec).any()


def test_feature_extraction_nan_inf_safety():
    """Verify NaNs and Infs are replaced by finite safe default values."""
    corrupt_dict = {
        "min_gap_m": float("nan"),
        "peak_closing_speed_ms": float("inf"),
        "speed_delta_kmh": -float("inf"),
    }
    feats = extract_features_from_dict(corrupt_dict)
    assert not np.isnan(feats["min_gap_m"])
    assert not np.isinf(feats["peak_closing_speed_ms"])
    assert not np.isinf(feats["speed_delta_kmh"])


# ==============================================================================
# 2. DATASET COHORT & LEAKAGE CONTROLS TESTS
# ==============================================================================

def test_canonical_monza_dataset_cohort():
    """Verify canonical Monza 2024 dataset contains both positive candidates and nominal controls."""
    dataset = build_canonical_monza_dataset()
    summary = dataset.summary()

    assert summary["total_samples"] >= 10
    assert summary["incident_candidates"] == 3  # The 3 empirical reference candidates
    assert summary["nominal_racing"] >= 7       # Nominal racing controls
    assert summary["unique_groups"] == summary["total_samples"]  # Strict group isolation

    # Test matrix shapes
    X, y = dataset.X, dataset.y
    assert X.shape[0] == len(dataset.samples)
    assert X.shape[1] == len(FEATURE_NAMES_V1)
    assert len(y) == len(dataset.samples)
    assert set(np.unique(y)) == {0, 1}


# ==============================================================================
# 3. MODEL TRAINING, PROBABILITY BOUNDS & CONTRIBUTIONS TESTS
# ==============================================================================

def test_candidate_classifier_fit_and_predict():
    """Verify candidate classifier trains and outputs probabilities strictly in [0.0, 1.0]."""
    clf = CandidateInteractionClassifier(c_reg=1.0)
    clf.fit()
    assert clf.is_fitted is True

    # Test extreme positive features (severe closure, near-zero gap, high trajectory dev)
    pos_features = extract_features_from_dict({
        "min_gap_m": 0.40,
        "peak_closing_speed_ms": 10.5,
        "mean_closing_speed_ms": 6.0,
        "speed_delta_kmh": 20.0,
        "brake_delta_pct": 50.0,
        "max_trajectory_dev_m": 2.50,
        "apex_overlap_pct": 75.0,
        "exit_clearance_m": 1.10,
    })
    p_pos = clf.predict_probability(pos_features)
    assert 0.0 <= p_pos <= 1.0
    assert p_pos >= 0.50  # Should be flagged as candidate pattern

    # Test clean nominal racing features (wide gap, low closing speed, minimal trajectory dev)
    neg_features = extract_features_from_dict({
        "min_gap_m": 4.50,
        "peak_closing_speed_ms": 1.2,
        "mean_closing_speed_ms": 0.4,
        "speed_delta_kmh": 2.0,
        "brake_delta_pct": 0.0,
        "max_trajectory_dev_m": 0.15,
        "apex_overlap_pct": 0.0,
        "exit_clearance_m": 3.80,
    })
    p_neg = clf.predict_probability(neg_features)
    assert 0.0 <= p_neg <= 1.0
    assert p_neg < 0.50   # Should NOT be flagged as candidate pattern
    assert p_pos > p_neg  # Monotonic ordering


def test_directional_feature_contributions():
    """Verify feature contributions return directional impact indicators and plain-English descriptions."""
    clf = get_candidate_classifier()
    features = extract_features_from_dict({
        "min_gap_m": 0.65,
        "peak_closing_speed_ms": 8.5,
        "max_trajectory_dev_m": 2.0,
    })
    contribs = clf.evaluate_contributions(features, top_k=5)
    assert len(contribs) == 5
    for c in contribs:
        assert c.feature_name in FEATURE_NAMES_V1
        assert isinstance(c.feature_value, float)
        assert isinstance(c.importance_weight, float)
        assert c.directional_impact in (
            "INCREASES_CANDIDATE_LIKELIHOOD",
            "DECREASES_CANDIDATE_LIKELIHOOD",
        )
        assert len(c.description) > 0


def test_evaluate_candidate_produces_valid_ml_evidence():
    """Verify evaluate_candidate returns fully populated MLEvidence schema with steward disclaimers."""
    clf = get_candidate_classifier()
    features = extract_features_from_dict({"min_gap_m": 0.80, "peak_closing_speed_ms": 7.0})
    evidence = clf.evaluate_candidate("TEST-CAND-01", features)

    assert isinstance(evidence, MLEvidence)
    assert evidence.incident_id == "TEST-CAND-01"
    assert 0.0 <= evidence.candidate_probability <= 1.0
    assert evidence.predicted_label in (0, 1)
    assert evidence.decision_threshold == 0.50
    assert evidence.classification in ("HIGH_CANDIDATE_LIKELIHOOD", "LOW_CANDIDATE_LIKELIHOOD")
    assert len(evidence.uncertainty_band) == 2
    assert evidence.uncertainty_band[0] <= evidence.uncertainty_band[1]
    assert len(evidence.top_contributing_features) > 0
    assert len(evidence.limitations) >= 2
    assert "DOES NOT evaluate fault" in evidence.steward_guidance


# ==============================================================================
# 4. BENCHMARK EVALUATION FRAMEWORK TESTS
# ==============================================================================

def test_benchmark_evaluation_report():
    """Verify leave-one-group-out cross validation report compares against Prompt 05/06 baseline."""
    evaluator = BenchmarkEvaluationReport()
    report = evaluator.evaluate_leave_one_group_out()

    assert "deterministic_baseline" in report
    det_base = report["deterministic_baseline"]
    assert det_base["recall"] == 1.000
    assert det_base["precision"] == 0.300
    assert det_base["f1_score"] == 0.4615

    assert "ml_model_cv_metrics" in report
    ml_metrics = report["ml_model_cv_metrics"]
    assert ml_metrics["total_samples"] >= 10
    assert 0.0 <= ml_metrics["precision"] <= 1.0
    assert 0.0 <= ml_metrics["recall"] <= 1.0
    assert 0.0 <= ml_metrics["f1_score"] <= 1.0
    assert 0.0 <= ml_metrics["specificity"] <= 1.0
    assert 0.0 <= ml_metrics["brier_score"] <= 1.0
    assert "confusion_matrix" in ml_metrics

    # Statistical honesty statement must be explicitly present
    assert "statistical_status" in report
    assert "PARTIAL" in report["statistical_status"]
    assert "honest_assessment" in report
    assert "Monza 2024" in report["honest_assessment"]


# ==============================================================================
# 5. REST API ENDPOINTS INTEGRATION TESTS
# ==============================================================================

def test_api_candidate_ml_evaluation_endpoint(client):
    """Test GET /api/v1/analysis/candidates/{candidate_id}/ml-evaluation."""
    response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/ml-evaluation")
    assert response.status_code == 200
    data = response.json()

    assert "candidateProbability" in data
    assert "predictedLabel" in data
    assert "classification" in data
    assert "decisionThreshold" in data
    assert "topContributingFeatures" in data
    assert "modelMetadata" in data
    assert "limitations" in data
    assert data["predictedLabel"] in (0, 1)
    assert 0.0 <= data["candidateProbability"] <= 1.0
    assert data["classification"] in ("HIGH_CANDIDATE_LIKELIHOOD", "LOW_CANDIDATE_LIKELIHOOD")


def test_api_benchmark_evaluation_endpoint(client):
    """Test GET /api/v1/analysis/ml/benchmark-evaluation."""
    response = client.get("/api/v1/analysis/ml/benchmark-evaluation")
    assert response.status_code == 200
    data = response.json()

    assert "deterministicBaseline" in data
    assert "mlModelCvMetrics" in data
    assert "statisticalStatus" in data
    assert "honestAssessment" in data
    assert data["deterministicBaseline"]["recall"] == 1.0


def test_api_frontend_incident_includes_ml_evidence(client):
    """Test GET /api/v1/analysis/candidates/{candidate_id}/frontend-incident includes mlEvidence."""
    response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/frontend-incident")
    assert response.status_code == 200
    data = response.json()

    assert "mlEvidence" in data
    assert data["mlEvidence"] is not None
    assert "candidateProbability" in data["mlEvidence"]
    assert "topContributingFeatures" in data["mlEvidence"]
    assert data["mlEvidence"]["incidentId"] in ("REF-MONZA-01", "CAND-2024-ITA-RIC_HUL-L1-01")


# ==============================================================================
# 6. FIA PROVENANCE & TECHNICAL REGULATION AUDIT TESTS
# ==============================================================================

def test_fia_provenance_audit_distinctions():
    """Verify FIA Technical Regulations (2.00m) are explicitly distinguished from engineering references (5.63m)."""
    guideline_ref = FIAGuidelineReference()
    assert guideline_ref.rule_source == "FIA Formula One Driving Standards Guidelines"
    assert "Article 3.3" in guideline_ref.width_reference_provenance
    assert "2000mm" in guideline_ref.width_reference_provenance
    assert "ENGINEERING_REFERENCE" in guideline_ref.length_reference_provenance
    assert "5.63m" in guideline_ref.length_reference_provenance
    assert "FIA_DRIVING_STANDARDS_GUIDELINES" in guideline_ref.guidelines_standard_provenance

    exit_metrics = ExitClearanceMetrics()
    assert exit_metrics.reference_width_threshold_m == 2.00
    assert "Article 3.3" in exit_metrics.reference_width_source


# ==============================================================================
# 7. PROMPT 11: MULTI-CIRCUIT DATASET, ROBUSTNESS & MODEL COMPARISON TESTS
# ==============================================================================

def test_missing_value_audit_observed_zero_vs_unobserved():
    """Verify observed zero sensor telemetry is distinguished from unobserved missing channels."""
    # Driver coasting with real 0% brake
    observed_coasting = {
        "min_gap_m": 2.5,
        "brake_delta_pct": 0.0,
        "missing_brake_flag": 0.0,
    }
    feats_coasting = extract_features_from_dict(observed_coasting)
    assert feats_coasting["brake_delta_pct"] == 0.0
    assert feats_coasting["missing_brake_flag"] == 0.0

    # Incomplete dossier missing brake channel entirely
    unobserved_sensor = {
        "min_gap_m": 2.5,
    }
    feats_unobserved = extract_features_from_dict(unobserved_sensor)
    assert feats_unobserved["brake_delta_pct"] == 0.0  # Sentinel default
    assert feats_unobserved["missing_brake_flag"] == 1.0  # Explicit missing flag


def test_multi_circuit_dataset_expansion_and_provenance():
    """Verify multi-circuit dataset spans Monza and Red Bull Ring with strict provenance."""
    dataset = build_canonical_dataset()
    summary = dataset.summary()

    assert summary["circuits_count"] >= 2
    assert "Monza" in summary["circuits"]
    assert "Red Bull Ring" in summary["circuits"]
    assert summary["total_samples"] >= 17
    assert summary["supervised_samples"] >= 15

    # Verify provenance on positive samples
    for sample in dataset.supervised_samples:
        if sample.label == 1:
            assert sample.provenance in (
                LabelProvenance.REFERENCE_INCIDENT,
                LabelProvenance.DOCUMENTED_INCIDENT,
            )
            assert "fia_document" in sample.metadata or len(sample.source) > 0, f"Sample {sample.sample_id} missing source document"
        elif sample.label == 0:
            assert sample.provenance == LabelProvenance.CONTROL_NOMINAL

    # Verify ambiguous / unverified samples are excluded from supervised training
    for sample in dataset.excluded_samples:
        assert sample.supervised_include is False
        assert sample.provenance == LabelProvenance.UNVERIFIED


def test_multi_model_classifiers_fit_and_predict():
    """Verify Random Forest and XGBoost classifiers fit and output calibrated probabilities."""
    dataset = build_canonical_dataset().get_supervised_dataset()

    # Random Forest
    rf = CandidateRandomForestClassifier(n_estimators=15, max_depth=3)
    rf.fit(dataset)
    assert rf.is_fitted is True
    p_rf = rf.predict_probability(dataset.samples[0].features)
    assert 0.0 <= p_rf <= 1.0

    # XGBoost
    xgb = CandidateXGBoostClassifier(n_estimators=20, max_depth=2)
    xgb.fit(dataset)
    assert xgb.is_fitted is True
    p_xgb = xgb.predict_probability(dataset.samples[0].features)
    assert 0.0 <= p_xgb <= 1.0


def test_leave_one_circuit_out_evaluation():
    """Verify Leave-One-Circuit-Out cross-validation executes without circuit leakage."""
    evaluator = BenchmarkEvaluationReport()
    loco_results = evaluator.evaluate_leave_one_circuit_out()

    assert "circuits_evaluated" in loco_results
    assert len(loco_results["circuits_evaluated"]) >= 2
    assert "fold_metrics" in loco_results
    assert len(loco_results["fold_metrics"]) >= 2
    for fold in loco_results["fold_metrics"]:
        assert fold["train_circuits"] != [fold["held_out_circuit"]]
        assert fold["test_support"] > 0
        assert 0.0 <= fold["brier_score"] <= 1.0


def test_api_ml_evaluation_extended_endpoint(client):
    """Test GET /api/v1/analysis/ml/evaluation returns multi-model comparisons and error analysis."""
    response = client.get("/api/v1/analysis/ml/evaluation")
    assert response.status_code == 200
    data = response.json()

    assert "modelComparison" in data
    assert "comparisonTable" in data
    assert "errorAnalysis" in data
    assert "datasetSummary" in data
    assert data["statisticalStatus"].startswith("PARTIAL")
    assert (data["datasetSummary"].get("circuits_count") or data["datasetSummary"].get("circuitsCount", 0)) >= 2
    assert len(data["comparisonTable"]) >= 4  # Baseline, LogReg, RF, XGBoost

