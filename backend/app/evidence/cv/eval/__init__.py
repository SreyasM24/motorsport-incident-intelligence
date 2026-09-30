"""CV Evaluation, Dataset Manifest & Ground Truth Benchmark Module."""

from app.evidence.cv.eval.contracts import (
    AnnotationCoordinateFormat,
    AnnotationIdentityStatus,
    AnnotationVisibility,
    CVEvaluationSuiteResponse,
    CrossModalEvaluationMetrics,
    DataProvenanceType,
    DatasetSampleManifest,
    DetectionEvaluationMetrics,
    FailureCategory,
    GroundTruthAnnotation,
    IdentityEvaluationMetrics,
    IncidentVisualEvidenceSufficiency,
    StewardReadinessRating,
    TrackingEvaluationMetrics,
    VideoAuthorizationStatus,
    VideoDatasetCatalog,
    VideoDatasetRecord,
    VideoSourceType,
    convert_normalized_to_pixel,
    convert_pixel_to_normalized,
    validate_annotation,
    validate_annotation_sequence,
)
from app.evidence.cv.eval.detector_eval import DetectionEvaluator
from app.evidence.cv.eval.tracker_eval import TrackingEvaluator
from app.evidence.cv.eval.identity_eval import IdentityEvaluator
from app.evidence.cv.eval.cross_modal_eval import CrossModalEvaluator
from app.evidence.cv.eval.split_manager import GroupSplitter
from app.evidence.cv.eval.service import CVEvaluationService, get_cv_evaluation_service

__all__ = [
    "AnnotationCoordinateFormat",
    "AnnotationIdentityStatus",
    "AnnotationVisibility",
    "CVEvaluationService",
    "CVEvaluationSuiteResponse",
    "CrossModalEvaluationMetrics",
    "CrossModalEvaluator",
    "DataProvenanceType",
    "DatasetSampleManifest",
    "DetectionEvaluationMetrics",
    "DetectionEvaluator",
    "FailureCategory",
    "GroundTruthAnnotation",
    "GroupSplitter",
    "IdentityEvaluationMetrics",
    "IdentityEvaluator",
    "IncidentVisualEvidenceSufficiency",
    "StewardReadinessRating",
    "TrackingEvaluationMetrics",
    "TrackingEvaluator",
    "VideoAuthorizationStatus",
    "VideoDatasetCatalog",
    "VideoDatasetRecord",
    "VideoSourceType",
    "convert_normalized_to_pixel",
    "convert_pixel_to_normalized",
    "get_cv_evaluation_service",
    "validate_annotation",
    "validate_annotation_sequence",
]
