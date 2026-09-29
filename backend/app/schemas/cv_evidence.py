"""Pydantic schemas and API contracts for Computer Vision Vehicle Detection and Tracking.

Re-exports contracts from app.evidence.cv.contracts for clean modularity.
"""

from app.evidence.cv.contracts import (
    BoundingBox,
    CVEvaluationReport,
    CVEvaluationStatus,
    CVIncidentAnalysisResponse,
    CVPerformanceMetrics,
    CVProcessingStatus,
    Detection,
    DetectionFrame,
    IdentityMethod,
    ModelStatus,
    Track,
    TrackInteractionFeature,
    TrackObservation,
    TrackQuality,
    TrackerResult,
    TrackingQualityRating,
    VisualIdentityAssociation,
)

__all__ = [
    "BoundingBox",
    "CVEvaluationReport",
    "CVEvaluationStatus",
    "CVIncidentAnalysisResponse",
    "CVPerformanceMetrics",
    "CVProcessingStatus",
    "Detection",
    "DetectionFrame",
    "IdentityMethod",
    "ModelStatus",
    "Track",
    "TrackInteractionFeature",
    "TrackObservation",
    "TrackQuality",
    "TrackerResult",
    "TrackingQualityRating",
    "VisualIdentityAssociation",
]
