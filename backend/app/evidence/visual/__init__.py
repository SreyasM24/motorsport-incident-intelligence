"""Visual evidence package providing bounded 2D features and multi-modal alignment."""

from app.evidence.visual.extractor import (
    VisualKeyframeExtractor,
    compute_cross_modal_alignment,
)
from app.evidence.visual.models import (
    AlignmentStatus,
    ApproachTrend,
    CrossModalAlignment,
    DriverAssociationStatus,
    VisibilityState,
    VisualEvidenceQuality,
    VisualEvidenceQualityRating,
    VisualEvidenceSummary,
    VisualFeatureEvidence,
    VisualKeyframe,
    VisualObservationStatus,
    VisualROI,
    VisualTrackObservation,
)
from app.evidence.visual.service import (
    VisualEvidenceService,
    get_visual_evidence_service,
)

__all__ = [
    "AlignmentStatus",
    "ApproachTrend",
    "CrossModalAlignment",
    "DriverAssociationStatus",
    "VisibilityState",
    "VisualEvidenceQuality",
    "VisualEvidenceQualityRating",
    "VisualEvidenceSummary",
    "VisualEvidenceService",
    "VisualFeatureEvidence",
    "VisualKeyframe",
    "VisualKeyframeExtractor",
    "VisualObservationStatus",
    "VisualROI",
    "VisualTrackObservation",
    "compute_cross_modal_alignment",
    "get_visual_evidence_service",
]
