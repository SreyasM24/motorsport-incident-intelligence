"""Motorsport Incident Intelligence - Machine Learning Readiness Layer.

Provides data preparation, tabular feature engineering, baseline models,
and evaluation framework for candidate interaction ranking without predicting guilt or fault.
"""

from app.schemas.ml_evidence import MLEvidence, FeatureContribution, MLModelMetadata
from app.ml.registry import (
    FeatureGovernanceStatus,
    FeatureEpistemicType,
    FeatureAvailability,
    FeatureGovernanceMetadata,
    get_feature_registry,
    is_feature_allowed,
    get_forbidden_feature_names,
    validate_feature_schema,
    audit_dictionary_for_forbidden_leakage,
)
from app.ml.dataset import (
    InclusionStatus,
    LabelProvenance,
    LabelSource,
    MLSample,
    MLDataset,
    build_canonical_dataset,
    build_multi_circuit_dataset,
)
from app.ml.features import (
    FEATURE_NAMES,
    FEATURE_VERSION,
    DEFAULT_FEATURE_VALUES,
    extract_features_from_dict,
    vectorize_features,
)
from app.ml.models import (
    CandidateInteractionClassifier,
    get_candidate_classifier,
)
from app.ml.evaluation import (
    BenchmarkEvaluationReport,
)

__all__ = [
    "MLEvidence",
    "FeatureContribution",
    "MLModelMetadata",
    "FeatureGovernanceStatus",
    "FeatureEpistemicType",
    "FeatureAvailability",
    "FeatureGovernanceMetadata",
    "get_feature_registry",
    "is_feature_allowed",
    "get_forbidden_feature_names",
    "validate_feature_schema",
    "audit_dictionary_for_forbidden_leakage",
    "InclusionStatus",
    "LabelProvenance",
    "LabelSource",
    "MLSample",
    "MLDataset",
    "build_canonical_dataset",
    "build_multi_circuit_dataset",
    "FEATURE_NAMES",
    "FEATURE_VERSION",
    "DEFAULT_FEATURE_VALUES",
    "extract_features_from_dict",
    "vectorize_features",
    "CandidateInteractionClassifier",
    "get_candidate_classifier",
    "BenchmarkEvaluationReport",
]

