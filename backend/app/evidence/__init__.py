"""Incident candidate reconstruction and multi-modal evidence fusion layer."""

from app.evidence.baseline_models import (
    BaselineDisruptionMetrics,
    BaselineEvidence,
    BaselineProfilePoint,
    BaselineStatus,
    DriverBaselineEvidence,
    ReferenceLapProvenance,
    SignalProvenanceInfo,
    SignalStatus,
    TrajectoryDeviationMetrics,
)
from app.evidence.candidate import (
    CandidateBatchResponse,
    CandidateDossier,
    CandidateEventType,
    CandidateQueryRequest,
    CandidateStatus,
    DataQualityFlags,
    EvidenceSignal,
    EvidenceSignalType,
)
from app.evidence.detector import DetectorConfig, MultiSignalDetector, TriggeredFrame
from app.evidence.dossier import (
    EvidenceDimensions,
    IncidentEvidenceDossier,
    convert_dossier_to_frontend_incident,
    synthesize_incident_evidence_dossier,
)
from app.evidence.evaluation import (
    MONZA_2024_REFERENCE_CASES,
    EvaluationMetrics,
    ReferenceIncidentCase,
    evaluate_candidates_against_ground_truth,
)
from app.evidence.event_builder import build_candidate_dossier, compute_evidence_strength
from app.evidence.features import FrameFeatures, extract_pairwise_features
from app.evidence.provenance import EvidenceProvenanceRecord, build_default_provenance
from app.evidence.race_control_evidence import (
    RaceControlEvidenceSummary,
    RaceControlMessageEvidence,
    build_race_control_evidence,
)
from app.evidence.reconstruction_service import (
    IncidentReconstructionEngine,
    get_reconstruction_engine,
)
from app.evidence.regulation_evidence import (
    EvidenceRegulationLink,
    RegulationEvidenceSummary,
    RegulationReference,
    match_relevant_regulations,
)
from app.evidence.segmenter import EpisodeSegmenter, SegmentedEpisode, SegmenterConfig
from app.evidence.telemetry_evidence import (
    TelemetryEvidenceSummary,
    build_telemetry_evidence,
)
from app.evidence.timeline import TimelineMilestone, generate_event_timeline
from app.evidence.video_evidence import (
    AnchorEventType,
    CalibrationPoint,
    CameraAlignmentInfo,
    IncidentVideoWindow,
    SynchronizedVideoFrame,
    SyncConfidence,
    SyncMethod,
    SynchronizationUncertainty,
    VideoClipRecommendation,
    VideoEvidenceSummary,
    VideoProvenanceRecord,
    VideoSourceMetadata,
    VideoSourceType,
    VideoSyncStatus,
    VideoTimeTransform,
    build_video_evidence,
    compute_calibration_transform,
    format_seconds_to_time,
    parse_timestamp_to_seconds,
)

__all__ = [
    "CandidateBatchResponse",
    "CandidateDossier",
    "CandidateEventType",
    "CandidateQueryRequest",
    "CandidateStatus",
    "DataQualityFlags",
    "DetectorConfig",
    "EpisodeSegmenter",
    "EvaluationMetrics",
    "EvidenceDimensions",
    "EvidenceProvenanceRecord",
    "EvidenceRegulationLink",
    "EvidenceSignal",
    "EvidenceSignalType",
    "FrameFeatures",
    "IncidentEvidenceDossier",
    "IncidentReconstructionEngine",
    "MONZA_2024_REFERENCE_CASES",
    "MultiSignalDetector",
    "RaceControlEvidenceSummary",
    "RaceControlMessageEvidence",
    "ReferenceIncidentCase",
    "RegulationEvidenceSummary",
    "RegulationReference",
    "SegmentedEpisode",
    "SegmenterConfig",
    "TelemetryEvidenceSummary",
    "TimelineMilestone",
    "TriggeredFrame",
    "AnchorEventType",
    "CalibrationPoint",
    "CameraAlignmentInfo",
    "IncidentVideoWindow",
    "SynchronizedVideoFrame",
    "SyncConfidence",
    "SyncMethod",
    "SynchronizationUncertainty",
    "VideoClipRecommendation",
    "VideoEvidenceSummary",
    "VideoProvenanceRecord",
    "VideoSourceMetadata",
    "VideoSourceType",
    "VideoSyncStatus",
    "VideoTimeTransform",
    "build_candidate_dossier",
    "build_default_provenance",
    "build_race_control_evidence",
    "build_telemetry_evidence",
    "build_video_evidence",
    "compute_evidence_strength",
    "convert_dossier_to_frontend_incident",
    "evaluate_candidates_against_ground_truth",
    "extract_pairwise_features",
    "generate_event_timeline",
    "get_reconstruction_engine",
    "match_relevant_regulations",
    "synthesize_incident_evidence_dossier",
]
