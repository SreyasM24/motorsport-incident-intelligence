"""Data contracts and schemas for CV Dataset, Ground Truth Annotation & Evaluation.

Strict Compliance & Guardrails (Prompt 15):
    1. Ground Truth vs Prediction Separation: Strictly distinguishes GROUND_TRUTH,
       MODEL_PREDICTION, and DERIVED_METRIC at every evaluation stage.
    2. Zero Autonomous Guilt or Fault: Visual metrics and evaluations are strictly descriptive.
       They NEVER assert driver fault, guilt, penalties, or collision verdicts.
    3. Explicit Coordinate System: Strict separation between NORMALIZED_0_1 and PIXEL_ABSOLUTE.
       Never mixed silently.
    4. Honest Status Reporting: When real-world broadcast footage or identity ground truth
       is absent, honestly reports NOT_AVAILABLE or INSUFFICIENT_DATA.
    5. Zero Data Leakage: Group-based splitting prevents frame-level temporal leakage.
"""

from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.evidence.cv.contracts import BoundingBox, CVProcessingStatus, TrackingQualityRating
from app.evidence.visual.models import AlignmentStatus, VisibilityState


# ==============================================================================
# 1. ENUMS & STATUS CODES
# ==============================================================================

class AnnotationCoordinateFormat(str, Enum):
    """Coordinate system representation for bounding boxes."""
    NORMALIZED_0_1 = "NORMALIZED_0_1"        # [xmin, ymin, xmax, ymax] in [0.0, 1.0]
    PIXEL_ABSOLUTE = "PIXEL_ABSOLUTE"        # [xmin, ymin, xmax, ymax] or [x, y, w, h] in pixels


class AnnotationIdentityStatus(str, Enum):
    """Ground truth identity annotation confidence."""
    CONFIRMED = "CONFIRMED"
    UNKNOWN = "UNKNOWN"
    NOT_ANNOTATED = "NOT_ANNOTATED"


class DataProvenanceType(str, Enum):
    """Explicit provenance origin of visual data."""
    GROUND_TRUTH = "GROUND_TRUTH"            # Certified ground-truth label
    MODEL_PREDICTION = "MODEL_PREDICTION"    # Raw hypothesis emitted by CV detector/tracker
    DERIVED_METRIC = "DERIVED_METRIC"        # Calculated geometric/kinematic feature


class FailureCategory(str, Enum):
    """Taxonomy of computer vision failure modes."""
    SMALL_VEHICLE = "SMALL_VEHICLE"
    DISTANT_VEHICLE = "DISTANT_VEHICLE"
    HEAVY_OCCLUSION = "HEAVY_OCCLUSION"
    OVERLAPPING_VEHICLES = "OVERLAPPING_VEHICLES"
    MOTION_BLUR = "MOTION_BLUR"
    POOR_LIGHTING = "POOR_LIGHTING"
    CAMERA_SHAKE = "CAMERA_SHAKE"
    PARTIAL_VISIBILITY = "PARTIAL_VISIBILITY"
    DETECTOR_MISS = "DETECTOR_MISS"
    DUPLICATE_DETECTION = "DUPLICATE_DETECTION"
    TRACK_FRAGMENTATION = "TRACK_FRAGMENTATION"
    IDENTITY_AMBIGUITY = "IDENTITY_AMBIGUITY"


class StewardReadinessRating(str, Enum):
    """Assessment of whether visual evidence is sufficient for human steward review."""
    SUFFICIENT = "SUFFICIENT"
    PARTIALLY_SUFFICIENT = "PARTIALLY_SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    UNAVAILABLE = "UNAVAILABLE"


# Alias for explicit annotation visibility contract
AnnotationVisibility = VisibilityState


# ==============================================================================
# 2. ANNOTATION CONTRACTS
# ==============================================================================

class GroundTruthAnnotation(BaseModel):
    """A ground truth visual vehicle annotation for a single frame."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    annotation_id: str
    frame_id: str
    object_id: str
    class_name: str = "vehicle"
    coordinate_format: AnnotationCoordinateFormat = AnnotationCoordinateFormat.NORMALIZED_0_1
    bounding_box: BoundingBox
    pixel_coords: Optional[Dict[str, int]] = None
    visibility: VisibilityState = VisibilityState.IN_FRAME
    occlusion: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = "HUMAN_EXPERT"
    provenance_type: DataProvenanceType = DataProvenanceType.GROUND_TRUTH
    track_id: Optional[str] = None
    identity_label: Optional[str] = None
    identity_status: AnnotationIdentityStatus = AnnotationIdentityStatus.NOT_ANNOTATED

    def to_normalized(self, frame_width: int, frame_height: int) -> BoundingBox:
        """Convert bounding box to normalized [0, 1] coordinates if stored in pixel format."""
        if self.coordinate_format == AnnotationCoordinateFormat.NORMALIZED_0_1:
            return self.bounding_box

        if self.pixel_coords:
            x, y, w, h = (
                self.pixel_coords.get("x", 0),
                self.pixel_coords.get("y", 0),
                self.pixel_coords.get("w", 0),
                self.pixel_coords.get("h", 0),
            )
            x_min = max(0.0, min(1.0, float(x) / frame_width))
            y_min = max(0.0, min(1.0, float(y) / frame_height))
            x_max = max(0.0, min(1.0, float(x + w) / frame_width))
            y_max = max(0.0, min(1.0, float(y + h) / frame_height))
            return BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)

        return self.bounding_box

    def to_pixel(self, frame_width: int, frame_height: int) -> Dict[str, int]:
        """Convert bounding box to integer pixel coordinates [x, y, w, h]."""
        if self.pixel_coords:
            return self.pixel_coords

        norm_box = self.bounding_box
        x = int(norm_box.x_min * frame_width)
        y = int(norm_box.y_min * frame_height)
        w = int(norm_box.width * frame_width)
        h = int(norm_box.height * frame_height)
        return {"x": x, "y": y, "w": w, "h": h}


class DatasetSampleManifest(BaseModel):
    """Manifest record identifying a video sample or frame."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    sample_id: str
    source_video: str
    frame_id: str
    frame_number: int
    timestamp_sec: float
    timestamp_str: str
    camera_id: str
    series: str = "Formula 1"
    event: str
    season: int
    session: str
    resolution: str
    fps: float
    annotation_status: str
    provenance_type: str = "OFFICIAL_COMMERCIAL_BROADCAST"
    license_provenance: str


# ==============================================================================
# 3. EVALUATION METRIC CONTRACTS
# ==============================================================================

class DetectionEvaluationMetrics(BaseModel):
    """Quantitative performance metrics for vehicle detection against ground truth."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_ground_truth: int = 0
    total_predictions: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    duplicate_detections: int = 0
    precision: float = Field(default=0.0, ge=0.0, le=1.0)
    recall: float = Field(default=0.0, ge=0.0, le=1.0)
    f1_score: float = Field(default=0.0, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    mean_iou: float = 0.0
    median_iou: float = 0.0
    min_iou: float = 0.0
    max_iou: float = 0.0
    ap_50: Optional[float] = None
    ap_75: Optional[float] = None
    breakdown_by_size: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    breakdown_by_occlusion: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class TrackingEvaluationMetrics(BaseModel):
    """Quantitative performance metrics for vehicle tracking against ground truth."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_gt_tracks: int = 0
    total_pred_tracks: int = 0
    id_switches: int = 0
    track_fragmentations: int = 0
    track_continuity_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_track_duration_sec: float = 0.0
    missed_observations: int = 0
    detection_errors: int = 0
    tracking_errors: int = 0
    mota: Optional[float] = None
    motp: Optional[float] = None
    statement: str = "Tracking evaluation measures continuity and ID persistence separate from detection."


class IdentityEvaluationMetrics(BaseModel):
    """Evaluation of driver identity attribution against ground truth."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evaluation_status: str = "NOT_AVAILABLE"
    total_evaluated: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    unknown_count: int = 0
    not_annotated_count: int = 0
    identity_accuracy: Optional[float] = None
    unknown_rate: Optional[float] = None
    incorrect_rate: Optional[float] = None
    statement: str = "Driver identity evaluation requires authoritative camera metadata or helmet/car livery annotations."


class CrossModalEvaluationMetrics(BaseModel):
    """Evaluation of visual-telemetry temporal alignment against ground truth."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evaluation_status: str = "NOT_AVAILABLE"
    total_events_evaluated: int = 0
    mean_absolute_difference_sec: Optional[float] = None
    median_difference_sec: Optional[float] = None
    max_difference_sec: Optional[float] = None
    uncertainty_interval_sec: Optional[float] = None
    aligned_count: int = 0
    partially_aligned_count: int = 0
    misaligned_count: int = 0
    statement: str = "Cross-modal evaluation measures temporal disparity between visual minimum separation and telemetry peak proximity."


# ==============================================================================
# 4. INCIDENT-LEVEL VISUAL EVIDENCE SUFFICIENCY (STEWARD DECISION SUPPORT)
# ==============================================================================

class IncidentVisualEvidenceSufficiency(BaseModel):
    """Incident-level visual evidence assessment answering:
    'Is there sufficient visual evidence for human steward inspection?'
    CRITICAL: Does NOT answer 'Who caused the incident?'.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    candidate_id: str
    video_available: bool = False
    synchronization_valid: bool = False
    vehicles_detected: bool = False
    tracks_continuous: bool = False
    identities_available: bool = False
    visual_interaction_features_available: bool = False
    telemetry_alignment_available: bool = False
    steward_readiness: StewardReadinessRating = StewardReadinessRating.UNAVAILABLE
    evaluation_summary: str
    limitations: List[str] = Field(default_factory=list)


# ==============================================================================
# 5. GLOBAL CV EVALUATION SUITE RESPONSE
# ==============================================================================

class CVEvaluationSuiteResponse(BaseModel):
    """Complete system-wide Computer Vision evaluation and dataset status report."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    real_video_status: str = "NOT_AVAILABLE"
    evaluation_status: str = "SYNTHETIC_VALIDATION_ONLY"
    dataset_state_classification: str = "SYNTHETIC_VALIDATION_ONLY"
    detection_metrics: Optional[DetectionEvaluationMetrics] = None
    tracking_metrics: Optional[TrackingEvaluationMetrics] = None
    identity_metrics: IdentityEvaluationMetrics = Field(default_factory=IdentityEvaluationMetrics)
    cross_modal_metrics: CrossModalEvaluationMetrics = Field(default_factory=CrossModalEvaluationMetrics)
    failure_categories: Dict[str, int] = Field(default_factory=dict)
    model_benchmarks: Dict[str, Any] = Field(default_factory=dict)
    performance: Dict[str, Any] = Field(default_factory=dict)
    provenance_summary: str
    steward_notice: str = (
        "EVALUATION PURPOSE ONLY: Visual metrics, detections, and tracks are descriptive evidence "
        "designed exclusively for human steward decision support. The system does not assign guilt, "
        "apportion fault, or determine collision liability."
    )


__all__ = [
    "AnnotationCoordinateFormat",
    "AnnotationIdentityStatus",
    "AnnotationVisibility",
    "CVEvaluationSuiteResponse",
    "CrossModalEvaluationMetrics",
    "DataProvenanceType",
    "DatasetSampleManifest",
    "DetectionEvaluationMetrics",
    "FailureCategory",
    "GroundTruthAnnotation",
    "IdentityEvaluationMetrics",
    "IncidentVisualEvidenceSufficiency",
    "StewardReadinessRating",
    "TrackingEvaluationMetrics",
]
