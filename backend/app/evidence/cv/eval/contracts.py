"""Data contracts and schemas for CV Dataset, Ground Truth Annotation & Evaluation.

Strict Compliance & Guardrails (Prompt 15 & Prompt 22):
    1. Ground Truth vs Prediction Separation: Strictly distinguishes GROUND_TRUTH,
       MODEL_PREDICTION, and DERIVED at every evaluation stage.
    2. Zero Autonomous Guilt or Fault: Visual metrics and evaluations are strictly descriptive.
       They NEVER assert driver fault, guilt, penalties, or collision verdicts.
    3. Explicit Coordinate System: Strict separation between NORMALIZED_0_1 and PIXEL_ABSOLUTE.
       Never mixed silently.
    4. Honest Status Reporting: When real-world broadcast footage or identity ground truth
       is absent, honestly reports INSUFFICIENT_DATA or NOT_AVAILABLE.
    5. Zero Data Leakage: Group-based splitting (LOVO / LOEO) prevents frame-level temporal leakage.
    6. Non-Adjudicative Discrepancy: Any cross-modal spatial or temporal discrepancy is an
       evidence-quality flag, NOT driver fault.
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
    GROUND_TRUTH = "GROUND_TRUTH"            # Certified ground-truth label (e.g. human expert)
    MODEL_PREDICTION = "MODEL_PREDICTION"    # Raw hypothesis emitted by CV detector/tracker
    DERIVED_METRIC = "DERIVED_METRIC"        # Calculated geometric/kinematic feature
    DERIVED = "DERIVED"                      # Generalized derived feature alias


class VideoSourceType(str, Enum):
    """Origin taxonomy of video footage."""
    BROADCAST_WORLD_FEED = "BROADCAST_WORLD_FEED"
    ONBOARD_CAMERA = "ONBOARD_CAMERA"
    TRACKSIDE_CCTV = "TRACKSIDE_CCTV"
    AUTHORIZED_RESEARCH_DATASET = "AUTHORIZED_RESEARCH_DATASET"
    SYNTHETIC_SIMULATION = "SYNTHETIC_SIMULATION"


class VideoAuthorizationStatus(str, Enum):
    """Legal and access authorization status of video stream."""
    AVAILABLE = "AVAILABLE"                  # Fully accessible & authorized
    AUTHORIZED = "AUTHORIZED"                # Authorized open research or licensed footage
    UNAUTHORIZED = "UNAUTHORIZED"            # Unauthorized stream/rip (NEVER treated as AVAILABLE)
    PENDING_REVIEW = "PENDING_REVIEW"        # Access or rights pending legal review
    UNAVAILABLE = "UNAVAILABLE"              # Commercially restricted / unbundled
    SYNTHETIC = "SYNTHETIC"                  # Synthetically generated fixture


class FailureCategory(str, Enum):
    """Taxonomy of computer vision failure modes (Prompt 22 12-category taxonomy + backward compatibility)."""
    # Canonical Prompt 22 12-category taxonomy
    DETECTION_MISS = "DETECTION_MISS"
    FALSE_DETECTION = "FALSE_DETECTION"
    OCCLUSION = "OCCLUSION"
    TRUNCATION = "TRUNCATION"
    TRACK_FRAGMENTATION = "TRACK_FRAGMENTATION"
    ID_SWITCH = "ID_SWITCH"
    IDENTITY_UNAVAILABLE = "IDENTITY_UNAVAILABLE"
    TIMESTAMP_MISALIGNMENT = "TIMESTAMP_MISALIGNMENT"
    CAMERA_GEOMETRY = "CAMERA_GEOMETRY"
    INSUFFICIENT_RESOLUTION = "INSUFFICIENT_RESOLUTION"
    VIDEO_UNAVAILABLE = "VIDEO_UNAVAILABLE"
    OTHER = "OTHER"

    # Additional fine-grained failure modes
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
# 2. COORDINATE CONVERSION & VALIDATION HELPERS
# ==============================================================================

def convert_normalized_to_pixel(bbox: BoundingBox, frame_width: int, frame_height: int) -> Dict[str, int]:
    """Convert normalized [0, 1] bounding box to integer pixel coordinates [x, y, w, h] with boundary clamping."""
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError(f"Invalid frame dimensions: width={frame_width}, height={frame_height}")

    x = max(0, min(frame_width - 1, int(round(bbox.x_min * frame_width))))
    y = max(0, min(frame_height - 1, int(round(bbox.y_min * frame_height))))
    w = max(1, min(frame_width - x, int(round(bbox.width * frame_width))))
    h = max(1, min(frame_height - y, int(round(bbox.height * frame_height))))
    return {"x": x, "y": y, "w": w, "h": h}


def convert_pixel_to_normalized(pixel_coords: Dict[str, int], frame_width: int, frame_height: int) -> BoundingBox:
    """Convert pixel coordinates [x, y, w, h] to normalized [0, 1] bounding box with boundary clamping."""
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError(f"Invalid frame dimensions: width={frame_width}, height={frame_height}")

    x = float(pixel_coords.get("x", 0))
    y = float(pixel_coords.get("y", 0))
    w = float(pixel_coords.get("w", 0))
    h = float(pixel_coords.get("h", 0))

    x_min = max(0.0, min(1.0, x / frame_width))
    y_min = max(0.0, min(1.0, y / frame_height))
    x_max = max(0.0, min(1.0, (x + w) / frame_width))
    y_max = max(0.0, min(1.0, (y + h) / frame_height))

    if x_max <= x_min:
        x_max = min(1.0, x_min + 1e-4)
    if y_max <= y_min:
        y_max = min(1.0, y_min + 1e-4)

    return BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)


# ==============================================================================
# 3. ANNOTATION & VIDEO DATASET CONTRACTS
# ==============================================================================

class GroundTruthAnnotation(BaseModel):
    """A ground truth visual vehicle annotation for a single frame."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    annotation_id: str
    frame_id: str
    object_id: str
    video_id: Optional[str] = None
    timestamp_sec: Optional[float] = None
    class_name: str = "vehicle"
    coordinate_format: AnnotationCoordinateFormat = AnnotationCoordinateFormat.NORMALIZED_0_1
    bounding_box: BoundingBox
    pixel_coords: Optional[Dict[str, int]] = None
    visibility: VisibilityState = VisibilityState.IN_FRAME
    occlusion: float = Field(default=0.0, ge=0.0, le=1.0)
    truncation: float = Field(default=0.0, ge=0.0, le=1.0)
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
            return convert_pixel_to_normalized(self.pixel_coords, frame_width, frame_height)

        return self.bounding_box

    def to_pixel(self, frame_width: int, frame_height: int) -> Dict[str, int]:
        """Convert bounding box to integer pixel coordinates [x, y, w, h]."""
        if self.pixel_coords:
            return self.pixel_coords

        return convert_normalized_to_pixel(self.bounding_box, frame_width, frame_height)


def validate_annotation(
    annotation: GroundTruthAnnotation,
    frame_width: Optional[int] = None,
    frame_height: Optional[int] = None,
) -> List[str]:
    """Validate a single annotation for coordinate bounds, visibility, occlusion, and truncation.

    Returns a list of validation error strings. If empty, the annotation is valid.
    """
    errors: List[str] = []

    # Coordinate bounds
    bb = annotation.bounding_box
    if bb.x_min < 0.0 or bb.x_min > 1.0:
        errors.append(f"x_min out of normalized bounds [0, 1]: {bb.x_min}")
    if bb.y_min < 0.0 or bb.y_min > 1.0:
        errors.append(f"y_min out of normalized bounds [0, 1]: {bb.y_min}")
    if bb.x_max < 0.0 or bb.x_max > 1.0:
        errors.append(f"x_max out of normalized bounds [0, 1]: {bb.x_max}")
    if bb.y_max < 0.0 or bb.y_max > 1.0:
        errors.append(f"y_max out of normalized bounds [0, 1]: {bb.y_max}")
    if bb.x_min >= bb.x_max:
        errors.append(f"Invalid bounding box width: x_min ({bb.x_min}) >= x_max ({bb.x_max})")
    if bb.y_min >= bb.y_max:
        errors.append(f"Invalid bounding box height: y_min ({bb.y_min}) >= y_max ({bb.y_max})")

    # Pixel coords bounds check if given
    if annotation.pixel_coords and frame_width and frame_height:
        px = annotation.pixel_coords
        x, y, w, h = px.get("x", 0), px.get("y", 0), px.get("w", 0), px.get("h", 0)
        if x < 0 or x >= frame_width:
            errors.append(f"Pixel x out of frame bounds [0, {frame_width}): {x}")
        if y < 0 or y >= frame_height:
            errors.append(f"Pixel y out of frame bounds [0, {frame_height}): {y}")
        if w <= 0 or (x + w) > frame_width:
            errors.append(f"Pixel box exceeds frame width {frame_width}: x={x}, w={w}")
        if h <= 0 or (y + h) > frame_height:
            errors.append(f"Pixel box exceeds frame height {frame_height}: y={y}, h={h}")

    # Occlusion & Truncation
    if annotation.occlusion < 0.0 or annotation.occlusion > 1.0:
        errors.append(f"Occlusion out of bounds [0, 1]: {annotation.occlusion}")
    if annotation.truncation < 0.0 or annotation.truncation > 1.0:
        errors.append(f"Truncation out of bounds [0, 1]: {annotation.truncation}")

    return errors


def validate_annotation_sequence(annotations: List[GroundTruthAnnotation]) -> List[str]:
    """Validate a sequence of annotations across frames for temporal monotonicity and track uniqueness.

    Returns a list of sequence validation error strings.
    """
    errors: List[str] = []
    if not annotations:
        return errors

    # Check for duplicate track IDs within the same frame
    frames_tracks: Dict[str, Set[str]] = {}
    for ann in annotations:
        f_id = ann.frame_id
        t_id = ann.track_id or ann.object_id
        if f_id not in frames_tracks:
            frames_tracks[f_id] = set()
        if t_id in frames_tracks[f_id]:
            errors.append(f"Duplicate track/object ID '{t_id}' detected in frame '{f_id}'.")
        else:
            frames_tracks[f_id].add(t_id)

    # Check temporal monotonicity per track if timestamps are provided
    tracks_timeline: Dict[str, List[Tuple[float, str]]] = {}
    for ann in annotations:
        if ann.timestamp_sec is not None:
            t_id = ann.track_id or ann.object_id
            tracks_timeline.setdefault(t_id, []).append((ann.timestamp_sec, ann.frame_id))

    for t_id, timeline in tracks_timeline.items():
        for i in range(1, len(timeline)):
            if timeline[i][0] < timeline[i - 1][0]:
                errors.append(
                    f"Non-monotonic timestamp detected for track '{t_id}': "
                    f"frame '{timeline[i][1]}' ({timeline[i][0]}s) < frame '{timeline[i-1][1]}' ({timeline[i-1][0]}s)."
                )

    return errors


class VideoDatasetRecord(BaseModel):
    """Manifest record for an individual video dataset entry."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    video_id: str
    series: str = "Formula 1"
    season: int = 2024
    event: str
    session: str = "RACE"
    camera_id: str
    source_type: VideoSourceType = VideoSourceType.BROADCAST_WORLD_FEED
    source_url: str
    license_status: str
    authorization_status: VideoAuthorizationStatus = VideoAuthorizationStatus.UNAVAILABLE
    duration_seconds: float = 0.0
    frame_rate: float = 30.0
    resolution: str = "1920x1080"
    timestamp_reference: str = "SESSION_ELAPSED_SEC"
    timezone: str = "UTC"
    incident_case_ids: List[str] = Field(default_factory=list)
    annotation_status: str = "UNANNOTATED"
    split: str = "TEST"
    provenance: str = ""
    content_hash: str = ""

    def is_accessible(self) -> bool:
        """Verify whether footage is legally accessible.

        CRITICAL INVARIANT: UNAUTHORIZED video is strictly NEVER treated as accessible.
        """
        if self.authorization_status == VideoAuthorizationStatus.UNAUTHORIZED:
            return False
        return self.authorization_status in {
            VideoAuthorizationStatus.AVAILABLE,
            VideoAuthorizationStatus.AUTHORIZED,
            VideoAuthorizationStatus.SYNTHETIC,
        }


class VideoDatasetCatalog(BaseModel):
    """Catalog summary of all cataloged video datasets and their authorization statuses."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    manifest_version: str = "2.0"
    dataset_name: str = "Motorsport Video & Computer Vision Evaluation Dataset"
    description: str = "Canonical catalog of real-world, research, and synthetic video records for motorsport CV evaluation."
    real_world_video_status: str = "INSUFFICIENT_DATA"
    license_policy: str = ""
    total_videos: int = 0
    total_duration_seconds: float = 0.0
    by_authorization_status: Dict[str, int] = Field(default_factory=dict)
    by_series: Dict[str, int] = Field(default_factory=dict)
    by_split: Dict[str, int] = Field(default_factory=dict)
    videos: List[VideoDatasetRecord] = Field(default_factory=list)
    dataset_card_url: str = "/data/cv/DATASET_CARD.md"


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
# 4. EVALUATION METRIC CONTRACTS
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

    evaluation_status: str = "INSUFFICIENT_DATA"
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
    spatial_discrepancy_m: Optional[float] = None
    spatial_alignment_status: Optional[str] = "NOT_EVALUATED"
    discrepancy_interpretation: str = "DISCREPANCY_IS_EVIDENCE_QUALITY_FLAG_NOT_DRIVER_FAULT"
    statement: str = "Cross-modal evaluation measures temporal disparity between visual minimum separation and telemetry peak proximity."


# ==============================================================================
# 5. INCIDENT-LEVEL VISUAL EVIDENCE SUFFICIENCY (STEWARD DECISION SUPPORT)
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
# 6. GLOBAL CV EVALUATION SUITE RESPONSE
# ==============================================================================

class CVEvaluationSuiteResponse(BaseModel):
    """Complete system-wide Computer Vision evaluation and dataset status report."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    real_world_video_status: str = "INSUFFICIENT_DATA"
    real_video_status: str = "NOT_AVAILABLE"
    evaluation_status: str = "SYNTHETIC_VALIDATION_ONLY"
    dataset_state_classification: str = "SYNTHETIC_VALIDATION_ONLY"
    dataset_catalog: Optional[VideoDatasetCatalog] = None
    detection_metrics: Optional[DetectionEvaluationMetrics] = None
    tracking_metrics: Optional[TrackingEvaluationMetrics] = None
    identity_metrics: IdentityEvaluationMetrics = Field(default_factory=IdentityEvaluationMetrics)
    cross_modal_metrics: CrossModalEvaluationMetrics = Field(default_factory=CrossModalEvaluationMetrics)
    failure_categories: Dict[str, int] = Field(default_factory=dict)
    splits_evaluation: Optional[Dict[str, Any]] = None
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
    "VideoAuthorizationStatus",
    "VideoDatasetCatalog",
    "VideoDatasetRecord",
    "VideoSourceType",
    "convert_normalized_to_pixel",
    "convert_pixel_to_normalized",
    "validate_annotation",
    "validate_annotation_sequence",
]
