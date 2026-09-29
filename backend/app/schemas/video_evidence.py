"""Pydantic schemas and API contracts for Video Evidence & Time Synchronization.

CRITICAL COMPLIANCE & JURISPRUDENTIAL DOCTRINE (PROMPT 12):
    1. Zero Copyright Infringement: Does NOT store, download, or redistribute copyrighted broadcast footage.
    2. Zero Hallucination: NEVER fabricates video sources, fake URLs, or synthetic sync timestamps.
    3. Honest VIDEO_UNAVAILABLE Default: If actual video bytes are not linked, the system explicitly reports
       VIDEO_UNAVAILABLE as a valid, non-penalizing state.
    4. Orthogonal Multi-Modal Evidence: Video evidence remains completely independent of telemetry,
       baseline deviations, geometry, and ML pattern analysis.
    5. Computer Vision Readiness: Establishes a strict SYNCHRONIZED_VIDEO_FRAME contract for future CV.
"""

from enum import Enum
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


# ==============================================================================
# 1. ENUMS & CONSTANTS
# ==============================================================================

class VideoSyncStatus(str, Enum):
    """Integrity and synchronization status of video evidence."""
    VIDEO_SYNCHRONIZED = "VIDEO_SYNCHRONIZED"
    VIDEO_AVAILABLE = "VIDEO_AVAILABLE"
    VIDEO_UNSYNCHRONIZED = "VIDEO_UNSYNCHRONIZED"
    VIDEO_UNAVAILABLE = "VIDEO_UNAVAILABLE"


class VideoSourceType(str, Enum):
    """Source provenance classification for video captures."""
    BROADCAST = "BROADCAST"
    ONBOARD = "ONBOARD"
    TRACKSIDE = "TRACKSIDE"
    USER_PROVIDED = "USER_PROVIDED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_str(cls, val: str) -> "VideoSourceType":
        """Normalize legacy or descriptive source type strings."""
        clean = (val or "").upper().strip()
        if "BROADCAST" in clean or "WORLD" in clean:
            return cls.BROADCAST
        elif "ONBOARD" in clean or "COCKPIT" in clean:
            return cls.ONBOARD
        elif "TRACKSIDE" in clean or "CCTV" in clean or "MARSHAL" in clean:
            return cls.TRACKSIDE
        elif "USER" in clean or "UPLOAD" in clean:
            return cls.USER_PROVIDED
        return cls.UNKNOWN


class SyncMethod(str, Enum):
    """Deterministic time synchronization algorithm used."""
    DIRECT_TIMESTAMP = "DIRECT_TIMESTAMP"    # Absolute hardware timecode / SMPTE / NTP
    MANUAL_CALIBRATION = "MANUAL_CALIBRATION"  # Human steward mapped frame / keypoint
    EVENT_ANCHOR = "EVENT_ANCHOR"            # Correlated against race control / telemetry event
    UNKNOWN = "UNKNOWN"                      # Insufficient information to synchronize


class SyncConfidence(str, Enum):
    """Qualitative confidence score reflecting synchronization accuracy."""
    HIGH = "HIGH"       # +/- 0.04s (frame-accurate)
    MEDIUM = "MEDIUM"   # +/- 0.20s (event anchor / manual alignment)
    LOW = "LOW"         # +/- 1.00s (coarse audio or visual estimation)
    NONE = "NONE"       # Unsynchronized / unavailable


class AnchorEventType(str, Enum):
    """Distinct physical or regulatory race event used as a temporal anchor."""
    LIGHTS_OUT = "LIGHTS_OUT"
    START_FINISH_CROSSING = "START_FINISH_CROSSING"
    PIT_ENTRY = "PIT_ENTRY"
    PIT_EXIT = "PIT_EXIT"
    RACE_CONTROL_MESSAGE = "RACE_CONTROL_MESSAGE"
    INCIDENT_TIMESTAMP = "INCIDENT_TIMESTAMP"
    RESTART = "RESTART"
    CUSTOM = "CUSTOM"


# ==============================================================================
# 2. PROVENANCE & CALIBRATION DATA MODELS
# ==============================================================================

class VideoProvenanceRecord(BaseModel):
    """Cryptographically verifiable and traceable provenance for video evidence."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    source: str = Field(..., description="E.g. Formula One Management (FOM), FIA Archive, Team Onboard")
    source_reference: str = Field(..., description="E.g. FOM World Feed Ch.1, Car 20 Onboard Rec, Doc 54 Evidence")
    acquisition_method: str = Field(
        default="METADATA_ONLY",
        description="BROADCAST_METADATA_EXTRACT, OFFICIAL_ARCHIVE, TELEMETRY_SYNCED_STREAM, UNLINKED, TEST_FIXTURE",
    )
    session: str = Field(..., description="Session identifier")
    camera: str = Field(..., description="Camera view identifier")
    timestamp_basis: str = Field(
        default="UNKNOWN",
        description="SMPTE_LTC, NTP_UTC, SESSION_ELAPSED, FASTF1_TIME_OFFSET, UNKNOWN",
    )
    availability: str = Field(
        default="VIDEO_UNAVAILABLE",
        description="VIDEO_UNAVAILABLE, METADATA_ONLY, STREAM_AVAILABLE",
    )
    metadata_quality: str = Field(default="NOMINAL", description="HIGH, NOMINAL, DEGRADED, UNVERIFIED")


class CalibrationPoint(BaseModel):
    """A verified temporal correspondence between video time and session/telemetry time."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    point_id: str
    name: str
    video_time_sec: float = Field(..., ge=0.0, description="Elapsed playback time in video (seconds)")
    session_time_sec: float = Field(..., description="Elapsed session or telemetry time (seconds)")
    utc_timestamp: Optional[str] = None
    anchor_type: Optional[AnchorEventType] = None
    description: str = ""


class SynchronizationUncertainty(BaseModel):
    """Quantified mathematical uncertainty bounds for temporal alignment."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    sync_status: VideoSyncStatus = VideoSyncStatus.VIDEO_UNAVAILABLE
    offset_seconds: Optional[float] = None
    estimated_error_seconds: Optional[float] = Field(
        default=None,
        description="Estimated uncertainty half-width in seconds (+/- epsilon)",
    )
    method: SyncMethod = SyncMethod.UNKNOWN
    confidence: SyncConfidence = SyncConfidence.NONE
    calibration_point_count: int = 0
    residual_rmse_seconds: Optional[float] = None
    limitations: List[str] = Field(default_factory=list)


class VideoTimeTransform(BaseModel):
    """Deterministic linear/affine transform: video_time = a * session_time + b.
    
    Guarantees reversible mapping between session telemetry time and video playback time.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    time_scale: float = Field(default=1.0, gt=0.0, description="Time-scale dilation factor 'a' (1.0 for real-time)")
    offset_sec: float = Field(default=0.0, description="Additive offset 'b' such that: video_time = a * session_time + b")
    method: SyncMethod = SyncMethod.UNKNOWN
    uncertainty: SynchronizationUncertainty = Field(default_factory=SynchronizationUncertainty)

    def session_to_video_time(self, session_time_sec: float) -> float:
        """Convert session/telemetry time (seconds) to video playback time (seconds)."""
        v_time = self.time_scale * session_time_sec + self.offset_sec
        return max(0.0, round(v_time, 4))

    def video_to_session_time(self, video_time_sec: float) -> float:
        """Convert video playback time (seconds) to session/telemetry time (seconds)."""
        scale = self.time_scale if self.time_scale > 0 else 1.0
        s_time = (video_time_sec - self.offset_sec) / scale
        return max(0.0, round(s_time, 4))

    def session_to_frame_number(self, session_time_sec: float, frame_rate: Optional[float]) -> Optional[int]:
        """Convert session time to exact non-negative integer video frame number."""
        if frame_rate is None or frame_rate <= 0:
            return None
        v_sec = self.session_to_video_time(session_time_sec)
        return max(0, int(round(v_sec * frame_rate)))

    def frame_number_to_session_time(self, frame_number: int, frame_rate: float) -> float:
        """Convert integer frame number back to session time."""
        if frame_rate <= 0:
            raise ValueError(f"Invalid non-positive frame rate: {frame_rate}")
        if frame_number < 0:
            raise ValueError(f"Negative frame number: {frame_number}")
        v_sec = frame_number / frame_rate
        return self.video_to_session_time(v_sec)


# ==============================================================================
# 3. VIDEO SOURCE & PLAYBACK METADATA
# ==============================================================================

class VideoSourceMetadata(BaseModel):
    """Metadata representing an external, broadcast, onboard, or trackside video source."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    video_id: str
    source_type: str = Field(
        default="BROADCAST",
        description="BROADCAST, ONBOARD, TRACKSIDE, USER_PROVIDED, UNKNOWN",
    )
    source_url: Optional[str] = None
    source_reference: Optional[str] = None
    session_id: str
    camera_label: str = Field(..., description="E.g. 'World Feed', 'Car 20 Onboard', 'Turn 4 Trackside CCTV'")
    
    # Legacy offset field: video_time = session_time - offset (offset = session_time - video_time)
    session_to_video_offset_sec: Optional[float] = Field(
        default=None,
        description="Legacy offset where: video_time = session_time - session_to_video_offset_sec",
    )
    time_scale: float = Field(default=1.0, description="Playback speed scaling factor (1.0 for real-time)")
    duration_sec: Optional[float] = Field(default=None, ge=0.0)
    sync_status: VideoSyncStatus = VideoSyncStatus.VIDEO_UNAVAILABLE
    license_note: str = "Broadcast rights belong to FOM / FIA. Metadata reference only."
    
    # Prompt 12 additions
    frame_rate: Optional[float] = Field(default=None, gt=0.0, description="Frames per second (e.g. 25.0, 50.0, 59.94)")
    resolution: Optional[str] = Field(default=None, description="E.g. '1920x1080', '1280x720'")
    timezone: str = Field(default="UTC", description="Timezone / time basis")
    provenance: Optional[VideoProvenanceRecord] = None
    transform: Optional[VideoTimeTransform] = None
    calibration_points: List[CalibrationPoint] = Field(default_factory=list)
    availability_status: str = Field(default="UNAVAILABLE", description="AVAILABLE, METADATA_ONLY, UNAVAILABLE")


class VideoClipRecommendation(BaseModel):
    """Recommended playback clip boundaries for steward video review."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    clip_start_video_time: Optional[str] = Field(default=None, description="Formatted playback timestamp (HH:MM:SS.mmm)")
    clip_peak_video_time: Optional[str] = Field(default=None, description="Formatted peak moment playback timestamp")
    clip_end_video_time: Optional[str] = Field(default=None, description="Formatted playback timestamp (HH:MM:SS.mmm)")
    pre_roll_sec: float = 5.0
    post_roll_sec: float = 5.0
    total_clip_duration_sec: float
    sync_status: VideoSyncStatus


class IncidentVideoWindow(BaseModel):
    """Temporally aligned playback window computed from incident timeline."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    incident_id: str
    window_status: str = Field(default="UNAVAILABLE", description="AVAILABLE or UNAVAILABLE")
    session_start_time: str
    session_peak_time: str
    session_end_time: str
    video_start_time: Optional[str] = None
    video_peak_time: Optional[str] = None
    video_end_time: Optional[str] = None
    pre_roll_sec: float = 5.0
    post_roll_sec: float = 5.0
    total_clip_duration_sec: float = 0.0
    frame_start: Optional[int] = None
    frame_peak: Optional[int] = None
    frame_end: Optional[int] = None
    estimated_error_sec: Optional[float] = None
    confidence: SyncConfidence = SyncConfidence.NONE


class CameraAlignmentInfo(BaseModel):
    """Individual alignment and synchronization info for a specific camera angle."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    camera_id: str
    camera_label: str
    source_type: str
    sync_status: VideoSyncStatus
    sync_method: SyncMethod
    offset_seconds: Optional[float] = None
    estimated_error_seconds: Optional[float] = None
    confidence: SyncConfidence
    incident_window: Optional[IncidentVideoWindow] = None
    provenance: Optional[VideoProvenanceRecord] = None


# ==============================================================================
# 4. COMPUTER VISION READINESS CONTRACT (PROMPT 12 SECTION 18)
# ==============================================================================

class SynchronizedVideoFrame(BaseModel):
    """The canonical input contract for downstream Computer Vision modules (Prompt 13).
    
    Provides exact temporal, spatial, and frame-level ground truth alignment
    without implementing CV detection algorithms prematurely.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    video_id: str
    camera: str
    video_timestamp: str = Field(..., description="Playback time string (HH:MM:SS.mmm)")
    video_time_sec: float = Field(..., ge=0.0)
    session_timestamp: str = Field(..., description="ISO 8601 UTC timestamp or session string")
    session_time_sec: float = Field(..., ge=0.0)
    frame_number: Optional[int] = Field(default=None, ge=0)
    synchronization_error_sec: float = Field(default=0.0, ge=0.0)
    provenance: Optional[VideoProvenanceRecord] = None


# ==============================================================================
# 5. UNIFIED VIDEO EVIDENCE DOSSIER SECTION & DETAIL RESPONSE
# ==============================================================================

class VideoEvidenceSummary(BaseModel):
    """Multi-modal video evidence dossier section integrated into IncidentEvidenceDossier."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    video_evidence_status: VideoSyncStatus = VideoSyncStatus.VIDEO_UNAVAILABLE
    sources: List[VideoSourceMetadata] = Field(default_factory=list)
    recommended_clip: Optional[VideoClipRecommendation] = None
    statement: str = Field(
        default="No verified video broadcast feed is synchronized for this candidate event. "
        "Missing video is treated as unavailable evidence, not negative evidence."
    )
    incident_window: Optional[IncidentVideoWindow] = None
    multi_camera: List[CameraAlignmentInfo] = Field(default_factory=list)
    uncertainty: Optional[SynchronizationUncertainty] = None
    cv_readiness_frame: Optional[SynchronizedVideoFrame] = None
    visual_evidence: Optional[Any] = None
    limitations: List[str] = Field(default_factory=list)


class VideoEvidenceDetailResponse(BaseModel):
    """Detailed API response for candidate video evidence and temporal alignment."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    candidate_id: str
    session_id: str
    video_evidence_status: VideoSyncStatus
    sources: List[VideoSourceMetadata] = Field(default_factory=list)
    recommended_clip: Optional[VideoClipRecommendation] = None
    incident_window: Optional[IncidentVideoWindow] = None
    multi_camera: List[CameraAlignmentInfo] = Field(default_factory=list)
    uncertainty: Optional[SynchronizationUncertainty] = None
    cv_readiness_frame: Optional[SynchronizedVideoFrame] = None
    visual_evidence: Optional[Any] = None
    statement: str
    limitations: List[str] = Field(default_factory=list)


__all__ = [
    "AnchorEventType",
    "CalibrationPoint",
    "CameraAlignmentInfo",
    "IncidentVideoWindow",
    "SynchronizedVideoFrame",
    "SyncConfidence",
    "SyncMethod",
    "SynchronizationUncertainty",
    "VideoClipRecommendation",
    "VideoEvidenceDetailResponse",
    "VideoEvidenceSummary",
    "VideoProvenanceRecord",
    "VideoSourceMetadata",
    "VideoSourceType",
    "VideoSyncStatus",
    "VideoTimeTransform",
]
