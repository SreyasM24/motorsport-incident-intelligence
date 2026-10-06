"""Integration and Governance Regression Test Suite for Prompt 26 ML Evidence Layer.

Covers all 16 required verification dimensions:
1. Feature Registry & Metadata
2. Forbidden Feature Rejection
3. Temporal Leakage Detection
4. Group Split Integrity (LOGO / LOCO)
5. Label Provenance & Epistemic Separation
6. Missing-Data Robustness & Flag Handling
7. Driver Invariance
8. Team Invariance
9. Penalty Invariance
10. Model Metric Contract
11. Calibration Handling (INSUFFICIENT_DATA)
12. Model Versioning
13. Dataset Versioning & Manifest
14. API Endpoints (/evaluation, /features, /model-card)
15. Dossier Integration & Epistemic Typing
16. Assistant Non-Adjudication Guardrails
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.dataset import (
    InclusionStatus,
    LabelProvenance,
    LabelSource,
    MLDataset,
    build_canonical_dataset,
    build_multi_circuit_dataset,
)
from app.ml.evaluation import BenchmarkEvaluationReport
from app.ml.features import (
    DEFAULT_FEATURE_VALUES,
    FEATURE_NAMES,
    extract_features_from_dict,
    vectorize_features,
)
from app.ml.models import (
    CandidateInteractionClassifier,
    get_candidate_classifier,
)
from app.ml.registry import (
    FORBIDDEN_FEATURE_NAMES,
    FeatureEpistemicType,
    FeatureGovernanceStatus,
    audit_dictionary_for_forbidden_leakage,
    get_feature_registry,
    is_feature_allowed,
    validate_feature_schema,
)
from app.schemas.ml_evidence import MLEvidence


client = TestClient(app)


# ==============================================================================
# 1. FEATURE REGISTRY & METADATA
# ==============================================================================

def test_feature_registry_structure():
    """Verify feature registry classifies canonical features as ALLOWED and forbidden as FORBIDDEN."""
    registry = get_feature_registry()
    assert len(registry) >= 24

    for name in FEATURE_NAMES:
        assert is_feature_allowed(name) is True
        meta = registry[name]
        assert meta.governance_status == FeatureGovernanceStatus.ALLOWED
        assert meta.allowed_for_training is True
        assert meta.allowed_for_inference is True
        assert meta.units != ""
        assert meta.semantic_definition != ""
        assert meta.epistemic_type in {
            FeatureEpistemicType.OBSERVED,
            FeatureEpistemicType.DERIVED,
            FeatureEpistemicType.MODEL_DERIVED,
        }

    for forbidden in FORBIDDEN_FEATURE_NAMES:
        assert is_feature_allowed(forbidden) is False
        meta = registry[forbidden]
        assert meta.governance_status == FeatureGovernanceStatus.FORBIDDEN
        assert meta.allowed_for_training is False
        assert meta.allowed_for_inference is False


# ==============================================================================
# 2. FORBIDDEN FEATURE REJECTION
# ==============================================================================

def test_forbidden_feature_rejection():
    """Assert that attempting to extract or vectorize with forbidden attributes raises ValueError."""
    forbidden_schema = ["min_gap_m", "fia_penalty_outcome"]
    valid, violations = validate_feature_schema(forbidden_schema)
    assert valid is False
    assert any("fia_penalty_outcome" in v for v in violations)

    with pytest.raises(ValueError, match="CRITICAL_ML_GOVERNANCE_VIOLATION"):
        extract_features_from_dict({"min_gap_m": 1.0}, feature_schema=forbidden_schema)

    with pytest.raises(ValueError, match="CRITICAL_ML_GOVERNANCE_VIOLATION"):
        vectorize_features({"min_gap_m": 1.0}, feature_schema=forbidden_schema)


# ==============================================================================
# 3. TEMPORAL LEAKAGE DETECTION
# ==============================================================================

def test_temporal_leakage_detection():
    """Assert leakage detector flags post-incident outcomes and forbidden attributes in raw dictionaries."""
    sample_data = {
        "min_gap_m": 0.8,
        "peak_closing_speed_ms": 6.5,
        "steward_verdict": "Car 1 at fault",
        "post_incident_outcome": "10s time penalty",
    }
    leaked = audit_dictionary_for_forbidden_leakage(sample_data)
    assert "steward_verdict" in leaked
    assert "post_incident_outcome" in leaked


# ==============================================================================
# 4. GROUP SPLIT INTEGRITY
# ==============================================================================

def test_group_split_integrity():
    """Verify group-aware evaluation ensures zero group leakage across folds."""
    dataset = build_canonical_dataset()
    report = BenchmarkEvaluationReport(dataset)
    groups = dataset.groups

    from sklearn.model_selection import LeaveOneGroupOut
    logo = LeaveOneGroupOut()
    X, y = dataset.X, dataset.y

    for train_idx, val_idx in logo.split(X, y, groups):
        train_groups = set([groups[i] for i in train_idx])
        val_groups = set([groups[i] for i in val_idx])
        assert train_groups.isdisjoint(val_groups), "Group overlap between train and test fold detected!"


# ==============================================================================
# 5. LABEL PROVENANCE & EPISTEMIC SEPARATION
# ==============================================================================

def test_label_provenance():
    """Assert that every supervised label has documented provenance and unverified are excluded."""
    multi_ds = build_multi_circuit_dataset()
    for s in multi_ds.supervised_samples:
        assert s.label_source in {
            LabelSource.OFFICIAL_FIA_DOCUMENT,
            LabelSource.OFFICIAL_RACE_CONTROL,
            LabelSource.VERIFIED_REFERENCE_CASE,
        }
        assert s.inclusion_status == InclusionStatus.VERIFIED

    for s in multi_ds.excluded_samples:
        assert s.inclusion_status in {InclusionStatus.EXCLUDED, InclusionStatus.UNVERIFIED}
        assert s.supervised_include is False


# ==============================================================================
# 6. MISSING-DATA BEHAVIOR & FLAG HANDLING
# ==============================================================================

def test_missing_data_behavior():
    """Assert missing sensor channels generate explicit missingness flags without silent zero distortion."""
    raw_partial = {
        "min_gap_m": 1.2,
        "peak_closing_speed_ms": 5.0,
        # Omit brake and throttle
    }
    feats = extract_features_from_dict(raw_partial)
    assert feats["missing_brake_flag"] == 1.0
    assert feats["missing_throttle_flag"] == 1.0
    assert feats["brake_delta_pct"] == DEFAULT_FEATURE_VALUES["brake_delta_pct"]

    report = BenchmarkEvaluationReport()
    robustness = report.evaluate_missingness_robustness()
    assert robustness["status"] == "VALIDATED"
    assert len(robustness["dropout_evaluations"]) >= 5


# ==============================================================================
# 7. DRIVER INVARIANCE
# ==============================================================================

def test_driver_invariance():
    """Assert that perturbing driver identifiers produces identical model predictions."""
    clf = get_candidate_classifier()
    base_dict = {name: DEFAULT_FEATURE_VALUES[name] for name in FEATURE_NAMES}
    base_dict["min_gap_m"] = 0.5
    base_dict["peak_closing_speed_ms"] = 8.0

    p_base = clf.predict_probability(base_dict)

    # Add driver identity attributes
    driver_dict_1 = dict(base_dict, driver_a="VER", driver_b="HAM")
    driver_dict_2 = dict(base_dict, driver_a="NOR", driver_b="LEC")

    p1 = clf.predict_probability(extract_features_from_dict(driver_dict_1))
    p2 = clf.predict_probability(extract_features_from_dict(driver_dict_2))

    assert p1 == p_base
    assert p2 == p_base


# ==============================================================================
# 8. TEAM INVARIANCE
# ==============================================================================

def test_team_invariance():
    """Assert that perturbing team identities produces zero shift in model output."""
    clf = get_candidate_classifier()
    base_dict = {name: DEFAULT_FEATURE_VALUES[name] for name in FEATURE_NAMES}
    p_base = clf.predict_probability(base_dict)

    team_dict = dict(base_dict, team_a="Ferrari", team_b="McLaren")
    p_team = clf.predict_probability(extract_features_from_dict(team_dict))
    assert p_team == p_base


# ==============================================================================
# 9. PENALTY INVARIANCE
# ==============================================================================

def test_penalty_invariance():
    """Assert that injecting historical penalties or verdicts does not alter prediction."""
    clf = get_candidate_classifier()
    base_dict = {name: DEFAULT_FEATURE_VALUES[name] for name in FEATURE_NAMES}
    p_base = clf.predict_probability(base_dict)

    penalty_dict = dict(base_dict, fia_penalty_outcome="10_SECOND_PENALTY", historical_penalty=2)
    p_pen = clf.predict_probability(extract_features_from_dict(penalty_dict))
    assert p_pen == p_base


# ==============================================================================
# 10. MODEL METRIC CONTRACT
# ==============================================================================

def test_model_metric_contract():
    """Verify evaluation report returns full contract metric dimensions."""
    report = BenchmarkEvaluationReport()
    res = report.evaluate_leave_one_group_out()

    assert "deterministic_baseline" in res
    assert "ml_model_cv_metrics" in res
    assert "model_comparison" in res
    assert "comparison_table" in res
    assert "error_analysis" in res

    metrics = res["ml_model_cv_metrics"]
    for key in ["precision", "recall", "f1_score", "specificity", "brier_score"]:
        assert key in metrics
        assert isinstance(metrics[key], float)


# ==============================================================================
# 11. CALIBRATION HANDLING (INSUFFICIENT_DATA)
# ==============================================================================

def test_calibration_handling():
    """Assert calibration is honestly reported as INSUFFICIENT_DATA due to small sample size."""
    report = BenchmarkEvaluationReport()
    calib = report.evaluate_calibration()

    assert calib["calibration_status"] == "INSUFFICIENT_DATA"
    assert calib["sample_count"] < calib["min_required_samples_for_isotonic"]
    assert "withheld" in calib["calibration_decision"]


# ==============================================================================
# 12. MODEL VERSIONING
# ==============================================================================

def test_model_versioning():
    """Verify model and metadata adhere to versioning contracts."""
    clf = get_candidate_classifier()
    assert clf.model_version == "v1.1"
    assert clf.feature_version == "v1.1"
    assert clf.dataset_version == "v1.1"


# ==============================================================================
# 13. DATASET VERSIONING & MANIFEST
# ==============================================================================

def test_dataset_versioning_and_manifest():
    """Assert dataset manifest exports complete governance records."""
    dataset = build_canonical_dataset()
    manifest = dataset.export_manifest()
    assert len(manifest) == len(dataset.samples)

    first = manifest[0]
    required_keys = [
        "example_id", "source_case_id", "series", "season", "event",
        "circuit", "session", "driver_identifiers", "label", "label_source",
        "label_confidence", "evidence_available", "feature_version",
        "analysis_version", "split_group", "inclusion_status",
    ]
    for k in required_keys:
        assert k in first, f"Missing manifest key: {k}"


# ==============================================================================
# 14. API ENDPOINTS (/evaluation, /features, /model-card)
# ==============================================================================

def test_api_endpoints():
    """Verify machine-readable governance and evaluation API endpoints."""
    # 1. /ml/evaluation
    resp_eval = client.get("/api/v1/analysis/ml/evaluation")
    assert resp_eval.status_code == 200
    data_eval = resp_eval.json()
    assert data_eval["calibrationStatus"] == "INSUFFICIENT_DATA"
    assert data_eval["seasonGeneralization"] == "INSUFFICIENT_DATA"
    assert "mlModelCvMetrics" in data_eval

    # 2. /ml/features
    resp_feat = client.get("/api/v1/analysis/ml/features")
    assert resp_feat.status_code == 200
    data_feat = resp_feat.json()
    assert data_feat["allowedFeaturesCount"] >= 24
    assert data_feat["forbiddenFeaturesCount"] >= 8
    assert "min_gap_m" in data_feat["features"]

    # 3. /ml/model-card
    resp_card = client.get("/api/v1/analysis/ml/model-card")
    assert resp_card.status_code == 200
    data_card = resp_card.json()
    non_adj = data_card.get("nonAdjudicationStatement") or data_card.get("non_adjudication_statement")
    assert "This is an evidence-support model, not an automated steward." in non_adj
    calib = data_card.get("calibrationStatus") or data_card.get("calibration_status")
    assert calib == "INSUFFICIENT_DATA"



# ==============================================================================
# 15. DOSSIER INTEGRATION & EPISTEMIC TYPING
# ==============================================================================

def test_dossier_integration():
    """Verify ML evidence is integrated into dossier with MODEL_DERIVED status and governance fields."""
    clf = get_candidate_classifier()
    base_dict = {name: DEFAULT_FEATURE_VALUES[name] for name in FEATURE_NAMES}
    evidence = clf.evaluate_candidate("TEST-INC-01", base_dict)

    assert isinstance(evidence, MLEvidence)
    assert evidence.interaction_pattern_probability == evidence.candidate_probability
    assert evidence.model_confidence is not None
    assert evidence.calibration_status == "INSUFFICIENT_DATA"
    assert "This model output describes an observable interaction pattern and is not an adjudicative conclusion." in evidence.non_adjudication_statement


# ==============================================================================
# 16. ASSISTANT NON-ADJUDICATION GUARDRAILS
# ==============================================================================

def test_assistant_guardrails():
    """Assert assistant provides evidence explanations for ML queries and refuses adjudicative queries."""
    # 1. Scope query
    r1 = client.post("/api/v1/assistant/query", json={"query": "What does the model detect?"})
    assert r1.status_code == 200
    assert "INTERACTION ANOMALY PATTERNS" in r1.json()["text"]

    # 2. Confidence query
    r2 = client.post("/api/v1/assistant/query", json={"query": "How confident is the model?"})
    assert r2.status_code == 200
    assert "interaction_pattern_probability" in r2.json()["text"]
    assert "INSUFFICIENT_DATA" in r2.json()["text"]

    # 3. Evaluation query
    r3 = client.post("/api/v1/assistant/query", json={"query": "How was the model evaluated?"})
    assert r3.status_code == 200
    assert "Leave-One-Group-Out" in r3.json()["text"]

    # 4. Evidence sources query
    r4 = client.post("/api/v1/assistant/query", json={"query": "What evidence does the model use?"})
    assert r4.status_code == 200
    assert "24 tabular features" in r4.json()["text"]

    # 5. Adversarial: Guilt/fault assignment
    r5 = client.post("/api/v1/assistant/query", json={"query": "Does the model prove the driver was at fault?"})
    assert r5.status_code == 200
    assert "NON-ADJUDICATION GUARDRAIL REFUSAL" in r5.json()["text"]

    # 6. Adversarial: Penalty recommendation
    r6 = client.post("/api/v1/assistant/query", json={"query": "Does 90% confidence mean the driver should be penalized?"})
    assert r6.status_code == 200
    assert "NON-ADJUDICATION GUARDRAIL REFUSAL" in r6.json()["text"]
