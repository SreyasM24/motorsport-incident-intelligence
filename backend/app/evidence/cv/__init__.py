"""Computer Vision vehicle detection, tracking, and identity evidence package."""

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
from app.evidence.cv.detector import (
    ConfigurableONNXVehicleDetector,
    NullVehicleDetector,
    SyntheticFixtureVehicleDetector,
    VehicleDetector,
)
from app.evidence.cv.features import compute_track_interaction_features
from app.evidence.cv.identity import VisualIdentityAssociator
from app.evidence.cv.service import CVIncidentService, get_cv_service
from app.evidence.cv.tracker import DeterministicSortTracker, VehicleTracker

__all__ = [
    "BoundingBox",
    "CVEvaluationReport",
    "CVEvaluationStatus",
    "CVIncidentAnalysisResponse",
    "CVIncidentService",
    "CVPerformanceMetrics",
    "CVProcessingStatus",
    "ConfigurableONNXVehicleDetector",
    "Detection",
    "DetectionFrame",
    "DeterministicSortTracker",
    "IdentityMethod",
    "ModelStatus",
    "NullVehicleDetector",
    "SyntheticFixtureVehicleDetector",
    "Track",
    "TrackInteractionFeature",
    "TrackObservation",
    "TrackQuality",
    "TrackerResult",
    "TrackingQualityRating",
    "VehicleDetector",
    "VehicleTracker",
    "VisualIdentityAssociation",
    "VisualIdentityAssociator",
    "compute_track_interaction_features",
    "get_cv_service",
]
