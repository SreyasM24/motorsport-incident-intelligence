"""Bounded Visual Evidence & Multi-Modal Alignment Data Models.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS (PROMPT 13):
    1. Zero Guilt / Fault Inference: Visual observations are strictly descriptive spatial measurements
       (ROIs, centroids, image-plane separation, IoU). They NEVER determine fault, guilt, penalty,
       or contact verdicts.
    2. Zero Hallucination: Never fabricates broadcast footage, fake URLs, or synthetic sync timestamps.
    3. Honest UNAVAILABLE Default: Real Grand Prix sessions without licensed broadcast streams (e.g. Monza 2024)
       honestly return UNAVAILABLE with explicit disclaimers.
    4. Test Fixture Isolation: Synthetic automated test fixtures are strictly labeled TEST_FIXTURE.
    5. Observation State Distinction: Clearly distinguishes OBSERVED, DERIVED, and UNAVAILABLE states.
       Never converts missing visual evidence into zeros or falsified measurements.
    6. 2D vs 3D Physical Boundary: 2D image-plane coordinates are perspective projections and must
       never be conflated with 3D world telemetry ground truth without calibrated camera models.
"""

from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.schemas.video_evidence import VideoProvenanceRecord


# ==============================================================================
# 1. ENUMS & STATUS CODES
# ==============================================================================

class VisualObservationStatus(str, Enum):
    """Integrity and availability status of visual evidence."""
    OBSERVED = "OBSERVED"        # Direct visual observation from linked footage or test fixture
    DERIVED = "DERIVED"          # Computed via camera projection or interpolation
    UNAVAILABLE = "UNAVAILABLE"  # No visual footage linked / unobserved


class DriverAssociationStatus(str, Enum):
    """Confidence level of associating a visual ROI/track with a specific competitor."""
    CONFIRMED = "CONFIRMED"      # Definitive identification (onboard, distinct livery, car number)
    INFERRED = "INFERRED"        # Inferred from telemetry grid/track order or relative positions
    UNAVAILABLE = "UNAVAILABLE"  # Competitor unidentifiable in visual frame


class VisibilityState(str, Enum):
    """Visibility of the subject in the camera frame."""
    IN_FRAME = "IN_FRAME"        # Fully visible within frame boundaries
    PARTIAL = "PARTIAL"          # Partially cropped by frame edge or structure
    OCCLUDED = "OCCLUDED"        # Significantly occluded by another vehicle or barrier
    OUT_OF_FRAME = "OUT_OF_FRAME"# Outside camera field of view


class ApproachTrend(str, Enum):
    """Trend of 2D image-plane separation between two tracked objects."""
    APPROACHING = "APPROACHING"  # Centroids are converging in the 2D image plane
    RECEDING = "RECEDING"        # Centroids are diverging in the 2D image plane
    STABLE = "STABLE"            # Separation is roughly invariant
    UNKNOWN = "UNKNOWN"          # Insufficient frames to determine motion trend


class AlignmentStatus(str, Enum):
    """Cross-modal alignment status between visual observations and telemetry data."""
    ALIGNED = "ALIGNED"                      # Visual and telemetry event timestamps coincide within tolerance
    PARTIALLY_ALIGNED = "PARTIALLY_ALIGNED"  # Coincide within extended uncertainty bounds
    MISALIGNED = "MISALIGNED"                # Discrepancy exceeds uncertainty threshold
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"  # Missing either telemetry or visual peak reference


class VisualEvidenceQualityRating(str, Enum):
    """Overall qualitative fidelity score for visual evidence."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNUSABLE = "UNUSABLE"


# ==============================================================================
# 2. BOUNDED REGIONS OF INTEREST (ROI) & OBJECT TRACKING
# ==============================================================================

class VisualROI(BaseModel):
    """A bounded 2D Region of Interest in the video image plane."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    roi_id: str
    camera_id: str
    frame_number: Optional[int] = None
    x_min: float = Field(..., ge=0.0, le=1.0, description="Normalized left coordinate [0, 1]")
    y_min: float = Field(..., ge=0.0, le=1.0, description="Normalized top coordinate [0, 1]")
    x_max: float = Field(..., ge=0.0, le=1.0, description="Normalized right coordinate [0, 1]")
    y_max: float = Field(..., ge=0.0, le=1.0, description="Normalized bottom coordinate [0, 1]")
    pixel_coords: Optional[Dict[str, int]] = Field(
        default=None,
        description="Optional absolute pixel coordinates {'x': int, 'y': int, 'w': int, 'h': int}",
    )
    coordinate_system: str = Field(
        default="NORMALIZED_TOP_LEFT",
        description="Origin at top-left: (0,0) is top-left, (1,1) is bottom-right",
    )
    label: Optional[str] = Field(default=None, description="Visual object label (e.g. 'CAR_MAG_20', 'APEX_KERB')")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Detection confidence score")
    provenance: Optional[VideoProvenanceRecord] = None

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

    def compute_iou(self, other: "VisualROI") -> float:
        """Compute 2D Intersection-over-Union (IoU) with another bounding box in normalized space."""
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


class VisualTrackObservation(BaseModel):
    """A single vehicle track observation within a specific frame."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    track_id: str
    driver_number: Optional[str] = Field(default=None, description="Racing car number, e.g. '20'")
    driver_code: Optional[str] = Field(default=None, description="Driver 3-letter code, e.g. 'MAG'")
    association_status: DriverAssociationStatus = DriverAssociationStatus.CONFIRMED
    centroid_x: float = Field(..., ge=0.0, le=1.0)
    centroid_y: float = Field(..., ge=0.0, le=1.0)
    bbox: VisualROI
    visibility: VisibilityState = VisibilityState.IN_FRAME
    detection_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    track_persistence_frames: int = Field(
        default=1,
        ge=0,
        description="Number of consecutive frames this track ID has been tracked",
    )
    provenance: Optional[VideoProvenanceRecord] = None


# ==============================================================================
# 3. BOUNDED VISUAL FEATURES & IMAGE-PLANE METRICS
# ==============================================================================

class VisualFeatureEvidence(BaseModel):
    """Quantitative features extracted from bounded visual observations in a single keyframe."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    feature_set_id: str
    centroid_displacement_px: Optional[float] = Field(
        default=None,
        description="Inter-frame pixel displacement of target centroid",
    )
    bbox_width_norm: float = Field(..., ge=0.0, le=1.0)
    bbox_height_norm: float = Field(..., ge=0.0, le=1.0)
    bbox_overlap_iou: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="2D image plane Intersection-over-Union between car A and car B",
    )
    image_plane_separation_norm: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Euclidean distance between centroids in normalized coordinate space",
    )
    approach_recede_trend: ApproachTrend = ApproachTrend.UNKNOWN
    track_persistence_count: int = Field(default=0, ge=0)
    occlusion_detected: bool = False
    occlusion_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    measurement_basis: str = Field(
        default="BOUNDED_2D_PROJECTION",
        description="2D perspective projection only. Does NOT establish 3D physical contact or fault.",
    )


# ==============================================================================
# 4. SYNCHRONIZED VISUAL KEYFRAME
# ==============================================================================

class VisualKeyframe(BaseModel):
    """A synchronized visual frame containing verified bounded observations and features."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    keyframe_id: str
    event_relative_time_sec: float = Field(
        ...,
        description="Seconds relative to candidate peak/apex (-2.0s to +2.0s)",
    )
    video_timestamp: str = Field(..., description="Playback time string (HH:MM:SS.mmm)")
    video_time_sec: float = Field(..., ge=0.0)
    session_timestamp: str = Field(..., description="Session ISO timestamp or elapsed time string")
    session_time_sec: float = Field(..., ge=0.0)
    frame_number: Optional[int] = Field(default=None, ge=0)
    camera_id: str
    camera_label: str
    observations: List[VisualTrackObservation] = Field(default_factory=list)
    rois: List[VisualROI] = Field(default_factory=list)
    features: Optional[VisualFeatureEvidence] = None
    synchronization_error_sec: float = Field(default=0.0, ge=0.0)
    alignment_status: AlignmentStatus = AlignmentStatus.ALIGNED
    provenance: Optional[VideoProvenanceRecord] = None


# ==============================================================================
# 5. CROSS-MODAL ALIGNMENT CHECK
# ==============================================================================

class CrossModalAlignment(BaseModel):
    """Multi-modal cross-check between telemetry metrics (e.g. min distance / apex) and visual features."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    telemetry_event_time_sec: float = Field(
        ...,
        description="Session elapsed seconds of telemetry peak closing speed / minimum gap",
    )
    visual_event_time_sec: Optional[float] = Field(
        default=None,
        description="Session elapsed seconds of visual minimum image separation",
    )
    delta_seconds: Optional[float] = Field(
        default=None,
        description="t_visual - t_telemetry in seconds",
    )
    synchronization_uncertainty_sec: float = Field(
        default=0.0,
        ge=0.0,
        description="Affine transform uncertainty bound from video synchronization",
    )
    tolerance_sec: float = Field(
        default=0.20,
        ge=0.0,
        description="Acceptable cross-modal synchronization tolerance threshold (seconds)",
    )
    alignment_status: AlignmentStatus = AlignmentStatus.INSUFFICIENT_DATA
    description: str = Field(
        default="Cross-modal verification comparing telemetry minimum distance with visual image-plane minimum separation.",
    )


# ==============================================================================
# 6. QUALITY ASSESSMENT & OVERALL SUMMARY
# ==============================================================================

class VisualEvidenceQuality(BaseModel):
    """Audit of visual evidence quality factors."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    quality_rating: VisualEvidenceQualityRating = VisualEvidenceQualityRating.HIGH
    frame_rate_fps: Optional[float] = None
    resolution: Optional[str] = None
    occlusion_frequency: float = Field(default=0.0, ge=0.0, le=1.0)
    sync_uncertainty_sec: float = Field(default=0.0, ge=0.0)
    average_track_persistence: float = Field(default=0.0, ge=0.0)
    notes: List[str] = Field(default_factory=list)


class VisualEvidenceSummary(BaseModel):
    """The master visual evidence summary section included in the Incident Evidence Dossier."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: VisualObservationStatus = VisualObservationStatus.UNAVAILABLE
    camera_id: Optional[str] = None
    camera_label: Optional[str] = None
    keyframes: List[VisualKeyframe] = Field(default_factory=list)
    track_observations: List[VisualTrackObservation] = Field(default_factory=list)
    cross_modal_alignment: Optional[CrossModalAlignment] = None
    quality: Optional[VisualEvidenceQuality] = None
    statement: str = Field(
        default="No verified visual broadcast footage or bounded ROI observations are linked for this incident. "
        "Unobserved visual evidence is treated as missing evidence, not negative evidence.",
    )
    limitations: List[str] = Field(default_factory=list)


__all__ = [
    "AlignmentStatus",
    "ApproachTrend",
    "CrossModalAlignment",
    "DriverAssociationStatus",
    "VisibilityState",
    "VisualEvidenceQuality",
    "VisualEvidenceQualityRating",
    "VisualEvidenceSummary",
    "VisualFeatureEvidence",
    "VisualKeyframe",
    "VisualObservationStatus",
    "VisualROI",
    "VisualTrackObservation",
]
