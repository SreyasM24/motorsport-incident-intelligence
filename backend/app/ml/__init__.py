"""Motorsport Incident Intelligence - Machine Learning Readiness Layer.

Provides data preparation, tabular feature engineering, baseline models,
and evaluation framework for candidate interaction ranking without predicting guilt or fault.
"""

from app.schemas.ml_evidence import MLEvidence, FeatureContribution, MLModelMetadata

__all__ = ["MLEvidence", "FeatureContribution", "MLModelMetadata"]
