"""Computer Vision Vehicle Detection, Tracking & Identity Data Contracts.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS (PROMPT 14):
    1. Zero Autonomous Guilt or Fault: CV detections and tracks are descriptive visual measurements.
       They NEVER assert driver fault, blame, sporting legality, or collision contact verdicts.
    2. Zero Copyright Infringement & Zero Video Fabrication: Does NOT fabricate real race video.
    3. Honest Status Transparency: Distinguishes AVAILABLE, MODEL_UNAVAILABLE, VIDEO_UNAVAILABLE,
       and INSUFFICIENT_DATA states. Never falsifies model weights or real-world accuracy claims.
    4. Model Decoupling: Detector and tracker are abstracted behind interfaces, supporting ONNX/YOLO/CPU/GPU.
    5. Perspective Projection Boundary: All 2D image measurements carry measurement_basis = BOUNDED_2D_PROJECTION.
    6. Non-Adjudicative Language: Disallows "guilty", "at fault", "penalty", "illegal move", or "collision confirmed".
"""

from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.schemas.video_evidence import VideoProvenanceRecord
from app.evidence.visual.models import (
    AlignmentStatus,
    ApproachTrend,
    DriverAssociationStatus,
    VisibilityState,
)


# ==============================================================================
# 1. ENUMS & STATUS CODES
# ==============================================================================

class CVProcessingStatus(str, Enum):
    """Execution status of the computer vision pipeline."""
    AVAILABLE = "AVAILABLE"                      # Full detection & tracking completed
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"      # Model weights file unconfigured or absent
    VIDEO_UNAVAILABLE = "VIDEO_UNAVAILABLE"      # Video stream unlinked / broadcast rights restricted
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"      # Insufficient frames or detections to form tracks
    PROCESSING_ERROR = "PROCESSING_ERROR"        # Controlled processing error


class ModelStatus(str, Enum):
    """Inference engine availability status."""
    LOADED = "LOADED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class TrackingQualityRating(str, Enum):
    """Deterministic quality classification for a vehicle track."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class IdentityMethod(str, Enum):
    """Deterministic method used to infer vehicle driver identity."""
    ONBOARD_CAMERA_FIXED = "ONBOARD_CAMERA_FIXED"          # Camera permanently mounted to specific car
    TELEMETRY_TRACK_ORDER = "TELEMETRY_TRACK_ORDER"        # Track position correlated with telemetry order
    MANUAL_STEWARD_OVERRIDE = "MANUAL_STEWARD_OVERRIDE"    # Human reviewer visual assignment
    UNASSOCIATED = "UNASSOCIATED"                          # Insufficient evidence to assign identity


class CVEvaluationStatus(str, Enum):
    """Honest evaluation benchmark status."""
    NOT_YET_AVAILABLE = "NOT_YET_AVAILABLE"
    SYNTHETIC_BENCHMARK_ONLY = "SYNTHETIC_BENCHMARK_ONLY"
    REAL_WORLD_EVALUATED = "REAL_WORLD_EVALUATED"


# ==============================================================================
# 2. BOUNDING BOX & DETECTION CONTRACTS
# ==============================================================================

class BoundingBox(BaseModel):
    """Deterministic 2D bounding box in normalized [0, 1] image-plane coordinates."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    x_min: float = Field(..., ge=0.0, le=1.0, description="Normalized left edge [0, 1]")
    y_min: float = Field(..., ge=0.0, le=1.0, description="Normalized top edge [0, 1]")
    x_max: float = Field(..., ge=0.0, le=1.0, description="Normalized right edge [0, 1]")
    y_max: float = Field(..., ge=0.0, le=1.0, description="Normalized bottom edge [0, 1]")
    pixel_coords: Optional[Dict[str, int]] = Field(
        default=None,
        description="Optional absolute pixel coordinates {'x': int, 'y': int, 'w': int, 'h': int}",
    )
    coordinate_system: str = Field(
        default="NORMALIZED_TOP_LEFT",
        description="Origin (0,0) at top-left, (1,1) at bottom-right",
    )

    @property
    def width(self) -> float:
        return max(0.0, self.x_max - self.x_min)

    @property
    def height(self) -> float:
        return max(0.0, self.y_max - self.y_min)

    @property
    def centroid(self) -> Tuple[float, float]:
        return ((self.x_min + self.x_max) / 2.0, (self.y_min + self.y_max) / 2.0)

    @property
    def area(self) -> float:
        return self.width * self.height

    def compute_iou(self, other: "BoundingBox") -> float:
        """Compute deterministic 2D Intersection-over-Union (IoU) with another bounding box."""
        inter_x_min = max(self.x_min, other.x_min)
        inter_y_min = max(self.y_min, other.y_min)
        inter_x_max = min(self.x_max, other.x_max)
        inter_y_max = min(self.y_max, other.y_max)

        if inter_x_max <= inter_x_min or inter_y_max <= inter_y_min:
            return 0.0

        intersection = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        union = self.area + other.area - intersection
        if union <= 0.0:
            return 0.0
        return round(float(intersection / union), 4)

    def centroid_distance(self, other: "BoundingBox") -> float:
        """Compute Euclidean distance between centroids in normalized coordinate space."""
        c1 = self.centroid
        c2 = other.centroid
        return round(math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2), 4)


class Detection(BaseModel):
    """A single vehicle detection hypothesis emitted by a VehicleDetector."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    detection_id: str
    bbox: BoundingBox
    class_name: str = Field(
        default="vehicle",
        description="Raw detector class (e.g. 'car', 'vehicle', 'f1_car'). NEVER automatically converted to driver.",
    )
    class_id: int = 0
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detector confidence score")
    provenance: Optional[VideoProvenanceRecord] = None
    source_metadata: Dict[str, Any] = Field(default_factory=dict)


class DetectionFrame(BaseModel):
    """A synchronized video frame bundled with its vehicle detections."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    frame_number: int = Field(..., ge=0)
    video_id: str
    camera_id: str
    video_timestamp: str = Field(..., description="Playback time string (HH:MM:SS.mmm)")
    video_time_sec: float = Field(..., ge=0.0)
    session_timestamp: Optional[str] = None
    session_time_sec: Optional[float] = None
    synchronization_error_sec: float = Field(default=0.0, ge=0.0)
    detections: List[Detection] = Field(default_factory=list)
    provenance: Optional[VideoProvenanceRecord] = None


# ==============================================================================
# 3. TRACK & TRACKING CONTRACTS
# ==============================================================================

class TrackObservation(BaseModel):
    """Observation of a tracked vehicle at a specific frame."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    observation_id: str
    frame_number: int
    video_time_sec: float
    session_time_sec: Optional[float] = None
    bbox: BoundingBox
    centroid_x: float
    centroid_y: float
    confidence: float
    visibility: VisibilityState = VisibilityState.IN_FRAME
    source_detection_id: Optional[str] = None
    is_interpolated: bool = False


class VisualIdentityAssociation(BaseModel):
    """Defensible association between a visual track and a competitor/driver."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    track_id: str
    candidate_id: str
    driver_code: Optional[str] = Field(default=None, description="e.g. 'MAG', 'HUL'")
    driver_number: Optional[str] = Field(default=None, description="e.g. '20', '27'")
    association_status: DriverAssociationStatus = DriverAssociationStatus.UNAVAILABLE
    method: IdentityMethod = IdentityMethod.UNASSOCIATED
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    provenance: Optional[VideoProvenanceRecord] = None


class TrackQuality(BaseModel):
    """Quantitative track quality metrics with deterministic rating."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    rating: TrackingQualityRating = TrackingQualityRating.INSUFFICIENT_DATA
    observation_count: int = 0
    track_duration_sec: float = 0.0
    visibility_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    minimum_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    maximum_gap_frames: int = 0
    fragmentation_count: int = 0
    thresholds_applied: Dict[str, Any] = Field(default_factory=dict)


class Track(BaseModel):
    """A multi-frame vehicle track sequence produced by a VehicleTracker."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    track_id: str
    class_name: str = "vehicle"
    first_frame: int
    last_frame: int
    observations: List[TrackObservation] = Field(default_factory=list)
    observation_count: int = 0
    duration_sec: float = 0.0
    is_active: bool = False
    quality: TrackQuality = Field(default_factory=TrackQuality)
    identity_association: Optional[VisualIdentityAssociation] = None


class TrackerResult(BaseModel):
    """Comprehensive output of multi-object tracking across a frame sequence."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tracks: List[Track] = Field(default_factory=list)
    active_tracks: List[Track] = Field(default_factory=list)
    terminated_tracks: List[Track] = Field(default_factory=list)
    total_tracks: int = 0
    frame_count: int = 0


# ==============================================================================
# 4. TRACK-LEVEL INTERACTION FEATURES
# ==============================================================================

class TrackInteractionFeature(BaseModel):
    """Pairwise quantitative spatial interaction between two tracks at a specific frame."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    frame_number: int
    video_time_sec: float
    session_time_sec: Optional[float] = None
    event_relative_time_sec: float
    track_id_a: str
    track_id_b: str
    driver_a_code: Optional[str] = None
    driver_b_code: Optional[str] = None
    centroid_separation_norm: float = Field(
        ...,
        ge=0.0,
        description="2D image plane centroid Euclidean distance in normalized coords",
    )
    bbox_overlap_iou: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="2D image plane Intersection-over-Union",
    )
    relative_approach_rate_norm_per_sec: Optional[float] = Field(
        default=None,
        description="Rate of change of 2D separation (negative = closing, positive = receding)",
    )
    relative_displacement_px: Optional[float] = None
    approach_recede_trend: ApproachTrend = ApproachTrend.UNKNOWN
    simultaneous_visibility: bool = True
    occlusion_detected: bool = False
    occlusion_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_detection_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    temporal_continuity: bool = True
    measurement_basis: str = Field(
        default="BOUNDED_2D_PROJECTION",
        description="2D perspective projection only. Does NOT establish 3D physical contact or fault.",
    )


# ==============================================================================
# 5. COMPUTATIONAL PERFORMANCE & EVALUATION METRICS
# ==============================================================================

class CVPerformanceMetrics(BaseModel):
    """Measured computational performance metrics."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    model_name: str = "Unconfigured / Null"
    model_version: str = "1.0"
    inference_device: str = "CPU"
    input_resolution: str = "1920x1080"
    processed_frames: int = 0
    processing_fps: float = 0.0
    total_processing_time_sec: float = 0.0
    source_fps: float = 30.0
    dropped_frames: int = 0


class CVEvaluationReport(BaseModel):
    """Honest evaluation dataset and benchmark status."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evaluation_status: CVEvaluationStatus = CVEvaluationStatus.NOT_YET_AVAILABLE
    benchmark_dataset: Optional[str] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    map_50: Optional[float] = None
    id_switches: Optional[int] = None
    track_fragmentation_rate: Optional[float] = None
    statement: str = Field(
        default="EVALUATION_STATUS: NOT_YET_AVAILABLE. No authorized, peer-reviewed labelled F1 broadcast "
        "bounding-box/tracking dataset is bundled. Detection accuracy metrics will not be fabricated.",
    )


# ==============================================================================
# 6. INCIDENT WINDOW CV ANALYSIS RESPONSE
# ==============================================================================

class CVIncidentAnalysisResponse(BaseModel):
    """Complete Computer Vision analysis response for a candidate incident window."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    candidate_id: str
    session_id: str
    processing_status: CVProcessingStatus = CVProcessingStatus.VIDEO_UNAVAILABLE
    model_status: ModelStatus = ModelStatus.NOT_CONFIGURED
    camera_id: Optional[str] = None
    camera_label: Optional[str] = None
    sampled_frame_count: int = 0
    dropped_frame_count: int = 0
    detections_count: int = 0
    tracks_count: int = 0
    detections: List[Detection] = Field(default_factory=list)
    tracks: List[Track] = Field(default_factory=list)
    identity_associations: List[VisualIdentityAssociation] = Field(default_factory=list)
    interaction_features: List[TrackInteractionFeature] = Field(default_factory=list)
    alignment_status: AlignmentStatus = AlignmentStatus.INSUFFICIENT_DATA
    performance: Optional[CVPerformanceMetrics] = None
    evaluation: CVEvaluationReport = Field(default_factory=CVEvaluationReport)
    statement: str = Field(
        default="Computer Vision vehicle detection and tracking analysis completed.",
    )
    limitations: List[str] = Field(default_factory=list)
    provenance: Optional[VideoProvenanceRecord] = None


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
