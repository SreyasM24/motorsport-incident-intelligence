"""Machine learning model architectures for incident candidate vs nominal racing classification.

CRITICAL JURISPRUDENTIAL GUARDRAILS (PROMPT 11):
    1. Models score CANDIDATE INTERACTION ANOMALY PATTERNS only.
    2. NEVER predict guilt, fault, driver blame, or penalty outcomes.
    3. Outputs are interpretable (coefficients / feature importances) and non-binding.
    4. Explicitly communicates decision thresholds, uncertainty bounds, and cross-circuit limitations.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from app.ml.dataset import MLDataset, build_canonical_dataset
from app.ml.features import (
    FEATURE_NAMES,
    FEATURE_NAMES_V1,
    FEATURE_VERSION,
    extract_features_from_dict,
    vectorize_features,
)
from app.schemas.ml_evidence import (
    FeatureContribution,
    MLEvidence,
    MLModelMetadata,
)

FEATURE_DESCRIPTIONS: Dict[str, str] = {
    "min_gap_m": "Minimum measured vehicle separation distance",
    "peak_closing_speed_ms": "Maximum rate of proximity closure",
    "mean_closing_speed_ms": "Average closure rate across approach phase",
    "speed_delta_kmh": "Vehicle speed differential at closest proximity",
    "brake_delta_pct": "Difference in peak braking pedal inputs",
    "throttle_delta_pct": "Difference in throttle application inputs",
    "accel_delta_g": "Longitudinal acceleration differential",
    "max_trajectory_dev_m": "Maximum lateral deviation from reference lap",
    "mean_trajectory_dev_m": "Average lateral trajectory deviation",
    "braking_onset_delta_m": "Displacement in initial braking onset vs reference lap",
    "apex_speed_dev_kmh": "Speed deviation from nominal clean apex speed",
    "apex_delta_s_m": "Longitudinal spacing delta at corner apex",
    "apex_overlap_pct": "Longitudinal overlap percentage at corner apex",
    "front_axle_gap_m": "Axle-to-axle longitudinal separation distance",
    "exit_clearance_m": "Measured spatial clearance at corner exit",
    "relative_position_code": "Longitudinal ordering code (ahead/alongside/behind)",
    "sync_flag": "Timestamp synchronization integrity flag",
    "missing_telemetry_flag": "Telemetry frames absent/unavailable indicator",
    "missing_brake_flag": "Brake sensor telemetry channel unobserved/missing indicator",
    "missing_throttle_flag": "Throttle sensor telemetry channel unobserved/missing indicator",
    "missing_baseline_flag": "Reference lap baseline comparison unavailable indicator",
    "missing_geometry_flag": "Corner overtake geometry computation unavailable indicator",
    "missing_exit_clearance_flag": "Corner exit clearance spatial channel unobserved indicator",
    "sample_density": "Telemetry frames per interaction window",
}


class CandidateInteractionClassifier:
    """Interpretable L2-regularized Logistic Regression classifier for candidate interaction ranking."""

    def __init__(self, c_reg: float = 1.0, decision_threshold: float = 0.50):
        self.c_reg = c_reg
        self.decision_threshold = decision_threshold
        self.model_version = "v1.1"
        self.feature_version = FEATURE_VERSION
        self.dataset_version = "v1.1"
        self.feature_schema = list(FEATURE_NAMES)
        
        self.scaler = StandardScaler()
        self.clf = LogisticRegression(
            penalty="l2",
            C=self.c_reg,
            solver="lbfgs",
            max_iter=1000,
            random_state=42,
        )
        self.is_fitted = False
        self.n_samples_trained = 0
        self.circuits_trained: List[str] = []

    def fit(self, dataset: Optional[MLDataset] = None) -> "CandidateInteractionClassifier":
        """Fit standard scaler and regularized logistic regression model on the cohort."""
        if dataset is None:
            dataset = build_canonical_dataset()

        self.feature_schema = list(dataset.feature_names)
        X = dataset.X
        y = dataset.y

        if len(y) < 2 or len(np.unique(y)) < 2:
            raise ValueError("Dataset requires at least 2 samples with both positive and negative classes.")

        X_scaled = self.scaler.fit_transform(X)
        self.clf.fit(X_scaled, y)
        self.is_fitted = True
        self.n_samples_trained = len(y)
        self.circuits_trained = sorted(list(set(dataset.circuit_groups)))
        return self

    def predict_probability(self, features: Dict[str, float]) -> float:
        """Estimate the probability that the interaction matches an incident candidate pattern."""
        if not self.is_fitted:
            self.fit()

        vec = vectorize_features(features, self.feature_schema).reshape(1, -1)
        vec_scaled = self.scaler.transform(vec)
        prob = float(self.clf.predict_proba(vec_scaled)[0, 1])
        return round(max(0.0, min(1.0, prob)), 4)

    def evaluate_contributions(
        self,
        features: Dict[str, float],
        top_k: int = 5,
    ) -> List[FeatureContribution]:
        """Compute directional feature contributions via standardized linear coefficients."""
        if not self.is_fitted:
            self.fit()

        vec = vectorize_features(features, self.feature_schema)
        mean = self.scaler.mean_
        scale = self.scaler.scale_
        safe_scale = np.where(scale == 0, 1.0, scale)
        z_scores = (vec - mean) / safe_scale
        coefs = self.clf.coef_[0]

        impacts = coefs * z_scores

        ranked_indices = np.argsort(np.abs(impacts))[::-1][:top_k]
        contributions: List[FeatureContribution] = []

        for idx in ranked_indices:
            feat_name = self.feature_schema[idx]
            val = float(vec[idx])
            weight = round(float(impacts[idx]), 3)
            direction = (
                "INCREASES_CANDIDATE_LIKELIHOOD"
                if weight > 0
                else "DECREASES_CANDIDATE_LIKELIHOOD"
            )
            desc = FEATURE_DESCRIPTIONS.get(feat_name, feat_name)
            contributions.append(
                FeatureContribution(
                    feature_name=feat_name,
                    feature_value=round(val, 2),
                    importance_weight=weight,
                    directional_impact=direction,
                    description=desc,
                )
            )

        return contributions

    def evaluate_candidate(
        self,
        incident_id: str,
        features: Dict[str, float],
    ) -> MLEvidence:
        """Produce complete structured MLEvidence payload for incident dossier integration."""
        if not self.is_fitted:
            self.fit()

        prob = self.predict_probability(features)
        predicted_label = 1 if prob >= self.decision_threshold else 0
        classification = (
            "HIGH_CANDIDATE_LIKELIHOOD"
            if predicted_label == 1
            else "LOW_CANDIDATE_LIKELIHOOD"
        )

        # Conservative uncertainty interval based on cohort sample scale
        margin = 0.10 if self.n_samples_trained >= 15 else 0.20
        lower = round(max(0.0, prob - margin), 3)
        upper = round(min(1.0, prob + margin), 3)

        top_contribs = self.evaluate_contributions(features, top_k=5)

        circuits_str = ", ".join(self.circuits_trained) if self.circuits_trained else "Monza, Red Bull Ring"
        limitations = [
            f"Model trained across multi-circuit reference cohort ({circuits_str}, N={self.n_samples_trained}).",
            "Dataset volume is expanded across multiple tracks but remains statistically limited for full production generalization.",
            "Features quantify kinematic and spatial proximity anomalies only. The system DOES NOT infer driver intent or fault.",
            "Decision threshold is calibrated at 0.50 for conservative candidate screening.",
        ]

        metadata = MLModelMetadata(
            model_name=f"LogisticRegression_L2_{self.model_version}",
            model_family="Standardized L2-Regularized Logistic Regression",
            feature_version=self.feature_version,
            dataset_version=self.dataset_version,
            training_sample_count=self.n_samples_trained,
            cross_validation_strategy="Leave-One-Circuit-Out & Leave-One-Group-Out",
            dataset_scope=f"Multi-Circuit Reference Cohort ({circuits_str})",
            validation_status="PROTOTYPE_MULTI_CIRCUIT_EVALUATION",
        )

        return MLEvidence(
            incident_id=incident_id,
            candidate_probability=prob,
            predicted_label=predicted_label,
            decision_threshold=self.decision_threshold,
            classification=classification,
            uncertainty_band=[lower, upper],
            top_contributing_features=top_contribs,
            model_metadata=metadata,
            limitations=limitations,
            steward_guidance=(
                "This empirical ML score quantifies kinematic anomaly patterns relative to normal racing interactions. "
                "It DOES NOT evaluate fault, guilt, breach of sporting code, or steward penalties. "
                "Final adjudication rests entirely with the human steward panel."
            ),
        )


class CandidateRandomForestClassifier:
    """Non-linear ensemble baseline model for candidate interaction ranking."""

    def __init__(self, n_estimators: int = 15, max_depth: int = 3, decision_threshold: float = 0.50):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.decision_threshold = decision_threshold
        self.model_name = "RandomForest_v1.1"
        self.clf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=42,
        )
        self.is_fitted = False
        self.feature_schema = list(FEATURE_NAMES)

    def fit(self, dataset: Optional[MLDataset] = None) -> "CandidateRandomForestClassifier":
        if dataset is None:
            dataset = build_canonical_dataset()
        self.feature_schema = list(dataset.feature_names)
        self.clf.fit(dataset.X, dataset.y)
        self.is_fitted = True
        return self

    def predict_probability(self, features: Dict[str, float]) -> float:
        if not self.is_fitted:
            self.fit()
        vec = vectorize_features(features, self.feature_schema).reshape(1, -1)
        prob = float(self.clf.predict_proba(vec)[0, 1])
        return round(max(0.0, min(1.0, prob)), 4)


class CandidateXGBoostClassifier:
    """Gradient boosted tree baseline model for candidate interaction ranking."""

    def __init__(self, n_estimators: int = 15, max_depth: int = 2, learning_rate: float = 0.1):
        self.model_name = "XGBoost_v1.1" if HAS_XGBOOST else "GradientBoosting_v1.1"
        self.feature_schema = list(FEATURE_NAMES)
        if HAS_XGBOOST:
            self.clf = xgb.XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                eval_metric="logloss",
                random_state=42,
            )
        else:
            self.clf = GradientBoostingClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=42,
            )
        self.is_fitted = False

    def fit(self, dataset: Optional[MLDataset] = None) -> "CandidateXGBoostClassifier":
        if dataset is None:
            dataset = build_canonical_dataset()
        self.feature_schema = list(dataset.feature_names)
        self.clf.fit(dataset.X, dataset.y)
        self.is_fitted = True
        return self

    def predict_probability(self, features: Dict[str, float]) -> float:
        if not self.is_fitted:
            self.fit()
        vec = vectorize_features(features, self.feature_schema).reshape(1, -1)
        prob = float(self.clf.predict_proba(vec)[0, 1])
        return round(max(0.0, min(1.0, prob)), 4)


@lru_cache()
def get_candidate_classifier() -> CandidateInteractionClassifier:
    """Singleton factory for fitted CandidateInteractionClassifier."""
    clf = CandidateInteractionClassifier()
    clf.fit()
    return clf


@lru_cache()
def get_random_forest_classifier() -> CandidateRandomForestClassifier:
    """Singleton factory for fitted CandidateRandomForestClassifier."""
    clf = CandidateRandomForestClassifier()
    clf.fit()
    return clf


@lru_cache()
def get_xgboost_classifier() -> CandidateXGBoostClassifier:
    """Singleton factory for fitted CandidateXGBoostClassifier."""
    clf = CandidateXGBoostClassifier()
    clf.fit()
    return clf
