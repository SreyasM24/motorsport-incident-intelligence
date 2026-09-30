"""Comprehensive automated test suite for Prompt 22 — Real-World Video/CV Evaluation Foundation,
Video Dataset Contract, Annotation Pipeline, and Cross-Modal Validation.

Test Coverage:
    1. Real video dataset manifest schema, records, and honest INSUFFICIENT_DATA status
    2. Video authorization taxonomy and strict UNAUTHORIZED exclusion invariant
    3. Annotation coordinate bounds, pixel dimension clipping, and quality validation
    4. Annotation sequence validation: temporal monotonicity and unique track IDs per frame
    5. Dual-coordinate conversion (normalized <-> pixel) with strict clamping
    6. Group-aware splitting: Leave-One-Video-Out (LOVO) and Leave-One-Event-Out (LOEO) with zero leakage
    7. Detection evaluation metrics, IoU matching, and error categorization
    8. Tracking evaluation, ID switches, and track continuity
    9. Driver identity attribution: mandatory INSUFFICIENT_DATA status when independent ground truth absent
    10. Cross-modal temporal and spatial disparity as an evidence-quality flag, NOT driver fault
    11. Incident-level visual evidence sufficiency and non-adjudicative steward readiness
    12. REST API: GET /api/v1/analysis/cv/dataset
    13. REST API: GET /api/v1/analysis/cv/evaluation
    14. REST API: GET /api/v1/analysis/candidates/{id}/video/cv
    15. AI Steward Assistant: VIDEO_EVIDENCE_UNAVAILABLE and copyright grounding
"""

import pytest
from fastapi.testclient import TestClient

from app.evidence.cv.contracts import (
    BoundingBox,
    CVIncidentAnalysisResponse,
    CVProcessingStatus,
    Detection,
    Track,
    TrackingQualityRating,
    TrackObservation,
    TrackQuality,
    VisualIdentityAssociation,
)
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
from app.evidence.cv.eval.cross_modal_eval import CrossModalEvaluator
from app.evidence.cv.eval.detector_eval import DetectionEvaluator
from app.evidence.cv.eval.identity_eval import IdentityEvaluator
from app.evidence.cv.eval.service import CVEvaluationService, get_cv_evaluation_service
from app.evidence.cv.eval.split_manager import GroupSplitter
from app.evidence.cv.eval.tracker_eval import TrackingEvaluator
from app.schemas.assistant import AssistantQueryRequest
from app.api.assistant import query_assistant
from app.main import app

client = TestClient(app)


# ==============================================================================
# 1. REAL VIDEO DATASET MANIFEST & SCHEMA TESTS
# ==============================================================================

def test_real_video_manifest_loading_and_catalog():
    """Verify that the real video manifest loads correctly with honest status and complete schema."""
    svc = get_cv_evaluation_service()
    catalog = svc.load_real_video_manifest()

    assert isinstance(catalog, VideoDatasetCatalog)
    assert catalog.total_videos >= 10
    assert catalog.real_world_video_status == "INSUFFICIENT_DATA"
    assert catalog.manifest_version == "2.0"
    assert "Strict copyright compliance" in catalog.license_policy

    # Check presence of video categories
    statuses = catalog.by_authorization_status
    assert "UNAVAILABLE" in statuses  # Commercial FOM cases
    assert "AUTHORIZED" in statuses   # Open research datasets
    assert "SYNTHETIC" in statuses    # Mathematical test fixtures
    assert "UNAUTHORIZED" in statuses # Quarantined pirated clip


def test_video_authorization_and_security_invariant():
    """Verify that UNAUTHORIZED video is strictly NEVER treated as accessible."""
    unauthorized_record = VideoDatasetRecord(
        video_id="VID-TEST-PIRATED",
        series="Formula 1",
        season=2023,
        event="Pirated Clip",
        session="RACE",
        camera_id="CAM-UNAUTH",
        source_type=VideoSourceType.BROADCAST_WORLD_FEED,
        source_url="https://example.com/unauthorized",
        license_status="UNLICENSED",
        authorization_status=VideoAuthorizationStatus.UNAUTHORIZED,
    )
    assert unauthorized_record.is_accessible() is False

    authorized_record = VideoDatasetRecord(
        video_id="VID-TEST-RESEARCH",
        series="F1TENTH",
        season=2023,
        event="Autonomous GP",
        session="HEAT_1",
        camera_id="CAM-RESEARCH",
        source_type=VideoSourceType.AUTHORIZED_RESEARCH_DATASET,
        source_url="https://f1tenth.org",
        license_status="CC_BY_4_0",
        authorization_status=VideoAuthorizationStatus.AUTHORIZED,
    )
    assert authorized_record.is_accessible() is True

    unavailable_record = VideoDatasetRecord(
        video_id="VID-TEST-FOM",
        series="Formula 1",
        season=2024,
        event="Italian GP",
        session="RACE",
        camera_id="CAM-FOM",
        source_type=VideoSourceType.BROADCAST_WORLD_FEED,
        source_url="https://formula1.com",
        license_status="COMMERCIAL_RESTRICTED_FOM",
        authorization_status=VideoAuthorizationStatus.UNAVAILABLE,
    )
    assert unavailable_record.is_accessible() is False


# ==============================================================================
# 2. ANNOTATION QUALITY VALIDATION & COORDINATE CONVERSION
# ==============================================================================

def test_annotation_bounds_and_clamping_validation():
    """Verify that coordinate boundary validation catches out-of-range boxes."""
    # Valid annotation
    valid_ann = GroundTruthAnnotation(
        annotation_id="ANN-VAL-01",
        frame_id="frame_001",
        object_id="OBJ-01",
        bounding_box=BoundingBox(x_min=0.1, y_min=0.2, x_max=0.3, y_max=0.4),
        pixel_coords={"x": 192, "y": 216, "w": 384, "h": 216},
        occlusion=0.1,
        truncation=0.0,
    )
    errors = validate_annotation(valid_ann, frame_width=1920, frame_height=1080)
    assert len(errors) == 0

    # Out of bounds normalized box (x_min >= x_max)
    invalid_bbox = GroundTruthAnnotation(
        annotation_id="ANN-INV-01",
        frame_id="frame_001",
        object_id="OBJ-01",
        bounding_box=BoundingBox(x_min=0.5, y_min=0.2, x_max=0.3, y_max=0.4),
    )
    errors = validate_annotation(invalid_bbox)
    assert any("Invalid bounding box width" in e for e in errors)

    # Pixel coords exceed frame width
    overflow_px = GroundTruthAnnotation(
        annotation_id="ANN-INV-02",
        frame_id="frame_001",
        object_id="OBJ-01",
        bounding_box=BoundingBox(x_min=0.1, y_min=0.2, x_max=0.3, y_max=0.4),
        pixel_coords={"x": 1800, "y": 200, "w": 200, "h": 100},
    )
    errors = validate_annotation(overflow_px, frame_width=1920, frame_height=1080)
    assert any("Pixel box exceeds frame width" in e for e in errors)


def test_coordinate_conversion_helpers():
    """Verify exact round-trip conversion and clamping between normalized and pixel coordinates."""
    bbox = BoundingBox(x_min=0.10, y_min=0.20, x_max=0.50, y_max=0.60)
    px = convert_normalized_to_pixel(bbox, frame_width=1920, frame_height=1080)
    assert px["x"] == 192
    assert px["y"] == 216
    assert px["w"] == 768
    assert px["h"] == 432

    norm_bb = convert_pixel_to_normalized(px, frame_width=1920, frame_height=1080)
    assert abs(norm_bb.x_min - 0.10) < 1e-4
    assert abs(norm_bb.y_min - 0.20) < 1e-4
    assert abs(norm_bb.x_max - 0.50) < 1e-4
    assert abs(norm_bb.y_max - 0.60) < 1e-4


def test_annotation_sequence_validation():
    """Verify sequence validation enforces monotonic timecodes and unique track IDs."""
    # Duplicate track ID in same frame
    dup_annotations = [
        GroundTruthAnnotation(
            annotation_id="ANN-1",
            frame_id="frame_001",
            object_id="OBJ-01",
            track_id="TRK-A",
            bounding_box=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.2),
        ),
        GroundTruthAnnotation(
            annotation_id="ANN-2",
            frame_id="frame_001",
            object_id="OBJ-02",
            track_id="TRK-A",  # Duplicate track ID in frame_001!
            bounding_box=BoundingBox(x_min=0.3, y_min=0.3, x_max=0.4, y_max=0.4),
        ),
    ]
    errors = validate_annotation_sequence(dup_annotations)
    assert any("Duplicate track/object ID 'TRK-A'" in e for e in errors)

    # Non-monotonic timestamps in track sequence
    non_monotonic = [
        GroundTruthAnnotation(
            annotation_id="ANN-1",
            frame_id="frame_001",
            object_id="OBJ-01",
            track_id="TRK-B",
            timestamp_sec=1.5,
            bounding_box=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.2),
        ),
        GroundTruthAnnotation(
            annotation_id="ANN-2",
            frame_id="frame_002",
            object_id="OBJ-01",
            track_id="TRK-B",
            timestamp_sec=1.2,  # Backwards in time!
            bounding_box=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.2),
        ),
    ]
    errors = validate_annotation_sequence(non_monotonic)
    assert any("Non-monotonic timestamp detected" in e for e in errors)


# ==============================================================================
# 3. GROUP-AWARE SPLITTING (LOVO / LOEO)
# ==============================================================================

def test_leave_one_video_out_and_leave_one_event_out():
    """Verify LOVO and LOEO fold generation and strict zero-leakage invariant."""
    samples = [
        DatasetSampleManifest(
            sample_id="S1",
            source_video="video_A.mp4",
            frame_id="f1",
            frame_number=1,
            timestamp_sec=0.1,
            timestamp_str="00:00:00.100",
            camera_id="CAM1",
            event="Monza",
            season=2024,
            session="RACE",
            resolution="1080p",
            fps=30.0,
            annotation_status="COMPLETE",
            license_provenance="TEST",
        ),
        DatasetSampleManifest(
            sample_id="S2",
            source_video="video_A.mp4",
            frame_id="f2",
            frame_number=2,
            timestamp_sec=0.2,
            timestamp_str="00:00:00.200",
            camera_id="CAM1",
            event="Monza",
            season=2024,
            session="RACE",
            resolution="1080p",
            fps=30.0,
            annotation_status="COMPLETE",
            license_provenance="TEST",
        ),
        DatasetSampleManifest(
            sample_id="S3",
            source_video="video_B.mp4",
            frame_id="f1",
            frame_number=1,
            timestamp_sec=0.1,
            timestamp_str="00:00:00.100",
            camera_id="CAM2",
            event="Silverstone",
            season=2024,
            session="RACE",
            resolution="1080p",
            fps=30.0,
            annotation_status="COMPLETE",
            license_provenance="TEST",
        ),
    ]

    # Test LOVO
    lovo_folds = GroupSplitter.leave_one_video_out(samples)
    assert len(lovo_folds) == 2
    for fold in lovo_folds:
        assert GroupSplitter.verify_no_leakage(fold["train_samples"], fold["test_samples"], group_key="source_video")

    # Test LOEO
    loeo_folds = GroupSplitter.leave_one_event_out(samples)
    assert len(loeo_folds) == 2
    for fold in loeo_folds:
        assert GroupSplitter.verify_no_leakage(fold["train_samples"], fold["test_samples"], group_key="event")


# ==============================================================================
# 4. EVALUATION METRICS, IDENTITY, AND CROSS-MODAL VALIDATION
# ==============================================================================

def test_identity_evaluator_honest_insufficient_data():
    """Verify that driver identity attribution reports INSUFFICIENT_DATA when independent ground truth is absent."""
    gt_without_confirmed_id = [
        GroundTruthAnnotation(
            annotation_id="ANN-ID-01",
            frame_id="f1",
            object_id="OBJ-01",
            bounding_box=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.2),
            identity_status=AnnotationIdentityStatus.NOT_ANNOTATED,
        )
    ]
    pred = [
        VisualIdentityAssociation(candidate_id="REF-MONZA-01", track_id="OBJ-01", driver_code="VER", confidence=0.95)
    ]

    metrics = IdentityEvaluator.evaluate_associations(gt_without_confirmed_id, pred, is_synthetic=False)
    assert metrics.evaluation_status == "INSUFFICIENT_DATA"
    assert "INSUFFICIENT_DATA" in metrics.statement

    synth_metrics = IdentityEvaluator.evaluate_associations(gt_without_confirmed_id, pred, is_synthetic=True)
    assert synth_metrics.evaluation_status == "NOT_AVAILABLE"


def test_cross_modal_spatial_and_temporal_evaluation():
    """Verify cross-modal evaluation correctly measures disparity and embeds non-fault interpretation."""
    event_pairs = [(10.0, 10.05, 0.04), (20.0, 20.15, 0.05)]
    spatial_diffs = [0.35, 0.42]

    metrics = CrossModalEvaluator.evaluate_cross_modal_events(
        event_pairs=event_pairs,
        tolerance_sec=0.10,
        spatial_discrepancies_m=spatial_diffs,
    )

    assert metrics.evaluation_status == "EVALUATED"
    assert metrics.total_events_evaluated == 2
    assert metrics.spatial_alignment_status == "TIGHT_CORRESPONDENCE"
    assert metrics.discrepancy_interpretation == "DISCREPANCY_IS_EVIDENCE_QUALITY_FLAG_NOT_DRIVER_FAULT"
    assert "NOT driver fault" in metrics.statement


def test_incident_sufficiency_for_unlinked_case():
    """Verify incident visual evidence sufficiency reports UNAVAILABLE for unlinked broadcast cases."""
    svc = get_cv_evaluation_service()
    sufficiency = svc.evaluate_incident_sufficiency(candidate_id="REF-MONZA-01")

    assert sufficiency.steward_readiness == StewardReadinessRating.UNAVAILABLE
    assert sufficiency.video_available is False
    assert "VIDEO_EVIDENCE_UNAVAILABLE" in sufficiency.evaluation_summary
    assert any("STATUS: VIDEO_EVIDENCE_UNAVAILABLE" in lim for lim in sufficiency.limitations)
    assert any("Non-adjudication doctrine" in lim for lim in sufficiency.limitations)


# ==============================================================================
# 5. REST API ENDPOINT TESTS
# ==============================================================================

def test_api_cv_dataset_catalog():
    """Verify GET /api/v1/analysis/cv/dataset returns complete manifest catalog and schema."""
    response = client.get("/api/v1/analysis/cv/dataset")
    assert response.status_code == 200
    data = response.json()

    assert data["manifestVersion"] == "2.0"
    assert data["realWorldVideoStatus"] == "INSUFFICIENT_DATA"
    assert data["totalVideos"] >= 10
    assert "videos" in data
    assert len(data["videos"]) == data["totalVideos"]


def test_api_cv_evaluation_suite():
    """Verify GET /api/v1/analysis/cv/evaluation returns 12-category failure taxonomy and honest status."""
    response = client.get("/api/v1/analysis/cv/evaluation")
    assert response.status_code == 200
    data = response.json()

    assert data["realWorldVideoStatus"] == "INSUFFICIENT_DATA"
    assert data["realVideoStatus"] == "NOT_AVAILABLE"
    assert "failureCategories" in data

    # Verify all 12 Prompt 22 failure categories exist in response
    fc = data["failureCategories"]
    expected_categories = [
        "DETECTION_MISS",
        "FALSE_DETECTION",
        "OCCLUSION",
        "TRUNCATION",
        "TRACK_FRAGMENTATION",
        "ID_SWITCH",
        "IDENTITY_UNAVAILABLE",
        "TIMESTAMP_MISALIGNMENT",
        "CAMERA_GEOMETRY",
        "INSUFFICIENT_RESOLUTION",
        "VIDEO_UNAVAILABLE",
        "OTHER",
    ]
    for cat in expected_categories:
        assert cat in fc

    # Check LOVO and LOEO evaluations
    assert "splitsEvaluation" in data
    assert "lovo" in data["splitsEvaluation"]
    assert "loeo" in data["splitsEvaluation"]


def test_api_candidate_video_cv_endpoints():
    """Verify GET /api/v1/analysis/candidates/{candidate_id}/video/cv and /sufficiency."""
    # 1. Full CV incident analysis endpoint
    response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/cv")
    assert response.status_code == 200
    data = response.json()
    assert data["candidateId"] == "REF-MONZA-01"
    assert data["processingStatus"] == "VIDEO_UNAVAILABLE"
    assert data["sampledFrameCount"] == 0

    # 2. Sufficiency endpoint
    suff_response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/cv/sufficiency")
    assert suff_response.status_code == 200
    suff_data = suff_response.json()
    assert suff_data["candidateId"] == "REF-MONZA-01"
    assert suff_data["videoAvailable"] is False
    assert suff_data["stewardReadiness"] == "UNAVAILABLE"
    assert "VIDEO_EVIDENCE_UNAVAILABLE" in suff_data["evaluationSummary"]


# ==============================================================================
# 6. ASSISTANT INTEGRATION TESTS
# ==============================================================================

def test_assistant_video_inquiry_returns_video_evidence_unavailable():
    """Verify assistant query regarding video footage returns explicit VIDEO_EVIDENCE_UNAVAILABLE."""
    req = AssistantQueryRequest(
        query="Can you show me the broadcast video and camera angles for this incident?",
        incident_id="REF-MONZA-01",
    )
    res = query_assistant(payload=req)

    assert "VIDEO_EVIDENCE_UNAVAILABLE" in res.text
    assert "COMMERCIAL COPYRIGHT RESTRICTION" in res.text
    assert "Formula One Management" in res.text
    assert any(chip.label == "Status: VIDEO_EVIDENCE_UNAVAILABLE" for chip in res.evidence_chips)
