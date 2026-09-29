"""Pydantic schemas and data contracts for Machine Learning Candidate Evaluation.

CRITICAL JURISPRUDENTIAL GUARDRAILS:
    1. The ML model evaluates empirical INTERACTION PATTERNS (Incident Candidate vs Nominal Racing).
    2. NEVER predicts guilt, fault, liability, penalty, or steward verdict.
    3. Serves strictly as non-binding decision-support for human stewards.
    4. Explicitly reports dataset volume constraints and calibration uncertainty.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class FeatureContribution(BaseModel):
    """Directional contribution of an individual telemetry/baseline/geometry feature."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    feature_name: str
    feature_value: float
    importance_weight: float
    directional_impact: str = Field(
        ...,
        description="INCREASES_CANDIDATE_LIKELIHOOD or DECREASES_CANDIDATE_LIKELIHOOD",
    )
    description: str = ""


class MLModelMetadata(BaseModel):
    """Provenance and architectural metadata for the candidate scoring model."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    model_name: str = "LogisticRegression_L2_v1.0"
    model_family: str = "Linear / Logistic Regression with L2 Regularization"
    feature_version: str = "v1.0"
    dataset_version: str = "v1.0"
    training_sample_count: int = 15
    cross_validation_strategy: str = "LeaveOneGroupOut (Pair/Session Isolation)"
    dataset_scope: str = "Italian Grand Prix (Monza 2024)"
    validation_status: str = "PROTOTYPE_READINESS (Single-circuit reference cohort)"


class MLEvidence(BaseModel):
    """Structured machine learning evidence payload integrated into the incident dossier."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    incident_id: str
    candidate_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model-estimated probability that observed interaction features represent an incident candidate pattern.",
    )
    predicted_label: int = Field(
        ...,
        description="Binary classification indicator: 1 = INCIDENT_CANDIDATE, 0 = NOMINAL_RACING",
    )
    decision_threshold: float = Field(
        default=0.50,
        description="Calibrated probability threshold for positive candidate classification",
    )
    classification: str = Field(
        ...,
        description="HIGH_CANDIDATE_LIKELIHOOD or LOW_CANDIDATE_LIKELIHOOD",
    )
    uncertainty_band: List[float] = Field(
        default_factory=lambda: [0.0, 1.0],
        description="Confidence / uncertainty interval [lower_bound, upper_bound] for candidate probability",
    )
    top_contributing_features: List[FeatureContribution] = Field(default_factory=list)
    model_metadata: MLModelMetadata = Field(default_factory=MLModelMetadata)
    limitations: List[str] = Field(default_factory=list)
    steward_guidance: str = Field(
        default="This empirical ML score quantifies kinematic anomaly patterns relative to normal racing interactions. "
        "It DOES NOT evaluate fault, guilt, breach of sporting code, or steward penalties. "
        "Final adjudication rests entirely with the human steward panel."
    )


class BenchmarkEvaluationResponse(BaseModel):
    """Structured response for ML cross-validation benchmark report."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    deterministic_baseline: Dict[str, Any]
    ml_model_cv_metrics: Dict[str, Any]
    statistical_status: str
    honest_assessment: str
    model_comparison: Optional[Dict[str, Any]] = None
    comparison_table: Optional[List[Dict[str, Any]]] = None
    error_analysis: Optional[Dict[str, Any]] = None
    dataset_summary: Optional[Dict[str, Any]] = None

