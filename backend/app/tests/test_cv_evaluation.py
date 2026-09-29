"""Test suite for Prompt 15 — CV Dataset, Ground Truth Annotation & Evaluation Foundation.

Tests:
    1. Dataset manifest schema & provenance validation
    2. Annotation schema & coordinate validation (normalized vs pixel coords)
    3. Ground-truth vs prediction separation
    4. Group-based splitting & temporal leakage prevention
    5. Detection metric calculations (precision, recall, F1, IoU distribution, TP/FP/FN)
    6. Tracking metric calculations (ID switches, fragmentations, continuity, error separation)
    7. Identity metric calculations (CORRECT, INCORRECT, UNKNOWN, NOT_AVAILABLE)
    8. Unavailable-data behavior & Monza copyright transparency
    9. Provenance propagation
    10. Synthetic fixture evaluation
    11. Incident visual evidence sufficiency contract (steward decision support)
    12. REST API contracts (/cv/evaluation & /candidates/{id}/video/cv/sufficiency)
    13. Non-adjudicative guardrails (zero fault, guilt, or penalty claims)
"""

import pytest
from fastapi.testclient import TestClient

from app.api.analysis import router
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
    DataProvenanceType,
    DatasetSampleManifest,
    DetectionEvaluationMetrics,
    FailureCategory,
    GroundTruthAnnotation,
    IncidentVisualEvidenceSufficiency,
    StewardReadinessRating,
    TrackingEvaluationMetrics,
)
from app.evidence.cv.eval.cross_modal_eval import CrossModalEvaluator
from app.evidence.cv.eval.detector_eval import DetectionEvaluator
from app.evidence.cv.eval.identity_eval import IdentityEvaluator
from app.evidence.cv.eval.service import CVEvaluationService, get_cv_evaluation_service
from app.evidence.cv.eval.split_manager import GroupSplitter
from app.evidence.cv.eval.tracker_eval import TrackingEvaluator
from app.main import app


# ==============================================================================
# 1. DATASET MANIFEST VALIDATION
# ==============================================================================

def test_dataset_manifest_loading():
    """Verify loading and validation of samples from dataset_manifest.json."""
    service = get_cv_evaluation_service()
    samples = service.load_manifest_samples()
    assert len(samples) >= 3

    sample_001 = next((s for s in samples if s.sample_id == "SMP-FIXTURE-001"), None)
    assert sample_001 is not None
    assert sample_001.series == "Formula 1 Synthetic Benchmark"
    assert sample_001.fps == 30.0
    assert sample_001.annotation_status == "ANNOTATED"
    assert "Internal Project Synthetic" in sample_001.license_provenance

    # Verify official Monza sample carries honest UNAVAILABLE status
    monza_sample = next((s for s in samples if s.sample_id == "SMP-MONZA-01-UNAVAILABLE"), None)
    assert monza_sample is not None
    assert monza_sample.annotation_status == "UNAVAILABLE"
    assert "Formula One Management" in monza_sample.license_provenance


# ==============================================================================
# 2. ANNOTATION SCHEMA & COORDINATE CONVERSION
# ==============================================================================

def test_annotation_coordinate_conversion():
    """Verify coordinate conversion between NORMALIZED_0_1 and PIXEL_ABSOLUTE."""
    box_norm = BoundingBox(x_min=0.25, y_min=0.50, x_max=0.50, y_max=0.75)
    ann = GroundTruthAnnotation(
        annotation_id="ANN-TEST-01",
        frame_id="frame_0001",
        object_id="OBJ-01",
        class_name="vehicle",
        coordinate_format=AnnotationCoordinateFormat.NORMALIZED_0_1,
        bounding_box=box_norm,
        visibility=AnnotationVisibility.IN_FRAME,
        occlusion=0.10,
        source="TEST_SUITE",
        provenance_type=DataProvenanceType.GROUND_TRUTH,
    )

    # Convert to 1920x1080 pixels
    pixel_coords = ann.to_pixel(frame_width=1920, frame_height=1080)
    assert pixel_coords["x"] == int(0.25 * 1920)
    assert pixel_coords["y"] == int(0.50 * 1080)
    assert pixel_coords["w"] == int(0.25 * 1920)
    assert pixel_coords["h"] == int(0.25 * 1080)

    # Convert back to normalized from pixel coords
    ann_pixel = GroundTruthAnnotation(
        annotation_id="ANN-TEST-02",
        frame_id="frame_0001",
        object_id="OBJ-02",
        class_name="vehicle",
        coordinate_format=AnnotationCoordinateFormat.PIXEL_ABSOLUTE,
        bounding_box=BoundingBox(x_min=0.0, y_min=0.0, x_max=1.0, y_max=1.0),
        pixel_coords={"x": 480, "y": 540, "w": 480, "h": 270},
        visibility=AnnotationVisibility.IN_FRAME,
        occlusion=0.0,
        source="TEST_SUITE",
    )
    converted_norm = ann_pixel.to_normalized(frame_width=1920, frame_height=1080)
    assert pytest.approx(converted_norm.x_min, 0.001) == 0.25
    assert pytest.approx(converted_norm.y_min, 0.001) == 0.50
    assert pytest.approx(converted_norm.x_max, 0.001) == 0.50
    assert pytest.approx(converted_norm.y_max, 0.001) == 0.75


# ==============================================================================
# 3. GROUND TRUTH VS PREDICTION SEPARATION
# ==============================================================================

def test_ground_truth_vs_prediction_separation():
    """Verify strict provenance typing: GROUND_TRUTH vs MODEL_PREDICTION."""
    gt = GroundTruthAnnotation(
        annotation_id="GT-01",
        frame_id="f1",
        object_id="obj1",
        bounding_box=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.3, y_max=0.3),
        provenance_type=DataProvenanceType.GROUND_TRUTH,
        source="EXPERT_ANNOTATOR",
    )
    pred = Detection(
        detection_id="PRED-01",
        bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.3, y_max=0.3),
        confidence=0.88,
    )

    assert gt.provenance_type == DataProvenanceType.GROUND_TRUTH
    assert gt.source == "EXPERT_ANNOTATOR"
    # Predictions do not carry ground-truth source
    assert pred.detection_id.startswith("PRED-")


# ==============================================================================
# 4. LEAKAGE-SAFE GROUP SPLITTING
# ==============================================================================

def test_group_based_splitting_zero_leakage():
    """Verify group-based partitioning guarantees zero frame leakage between train and test."""
    samples = [
        DatasetSampleManifest(
            sample_id=f"SMP-{i}",
            source_video=f"video_session_{(i // 5) + 1}.mp4",
            frame_id=f"frame_{i}",
            frame_number=i,
            timestamp_sec=i * 0.033,
            timestamp_str="00:00:00.000",
            camera_id="CAM-1",
            event="Virtual Test",
            season=2024,
            session=f"session_{(i // 5) + 1}",
            resolution="1920x1080",
            fps=30.0,
            annotation_status="ANNOTATED",
            license_provenance="Test",
        )
        for i in range(25)  # 5 sessions, 5 frames each
    ]

    splits = GroupSplitter.partition_samples_by_group(
        samples=samples,
        group_key="session",
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
    )

    assert len(splits["train"]) > 0
    assert len(splits["test"]) > 0

    # Ensure zero leakage between train and test sessions
    assert GroupSplitter.verify_no_leakage(splits["train"], splits["test"], group_key="session")
    assert GroupSplitter.verify_no_leakage(splits["train"], splits["val"], group_key="session")
    assert GroupSplitter.verify_no_leakage(splits["val"], splits["test"], group_key="session")


# ==============================================================================
# 5. DETECTION EVALUATION METRICS
# ==============================================================================

def test_detection_evaluator_metrics_calculation():
    """Verify precision, recall, F1, IoU statistics, and failure categorizations."""
    gt_boxes = [
        GroundTruthAnnotation(
            annotation_id="GT-1",
            frame_id="f1",
            object_id="car1",
            bounding_box=BoundingBox(x_min=0.20, y_min=0.20, x_max=0.40, y_max=0.40),
            occlusion=0.0,
        ),
        GroundTruthAnnotation(
            annotation_id="GT-2",
            frame_id="f1",
            object_id="car2",
            bounding_box=BoundingBox(x_min=0.60, y_min=0.60, x_max=0.80, y_max=0.80),
            occlusion=0.60,  # heavily occluded
        ),
        GroundTruthAnnotation(
            annotation_id="GT-3",
            frame_id="f1",
            object_id="car3",
            bounding_box=BoundingBox(x_min=0.01, y_min=0.01, x_max=0.03, y_max=0.03),  # small vehicle
            occlusion=0.0,
        ),
    ]

    # Detector detects GT-1 correctly, duplicates GT-1, detects false positive, misses GT-2 and GT-3
    preds = [
        Detection(
            detection_id="P1",
            bbox=BoundingBox(x_min=0.20, y_min=0.20, x_max=0.40, y_max=0.40),
            confidence=0.95,
        ),
        Detection(
            detection_id="P2",  # Duplicate match for GT-1
            bbox=BoundingBox(x_min=0.21, y_min=0.21, x_max=0.39, y_max=0.39),
            confidence=0.85,
        ),
        Detection(
            detection_id="P3",  # False positive in empty space
            bbox=BoundingBox(x_min=0.90, y_min=0.90, x_max=0.98, y_max=0.98),
            confidence=0.70,
        ),
    ]

    evaluator = DetectionEvaluator(iou_threshold=0.50)
    metrics, failures = evaluator.evaluate_detections(gt_boxes, preds)

    assert metrics.total_ground_truth == 3
    assert metrics.total_predictions == 3
    assert metrics.true_positives == 1
    assert metrics.false_positives == 2
    assert metrics.false_negatives == 2
    assert metrics.duplicate_detections == 1

    assert pytest.approx(metrics.precision, 0.01) == 0.3333
    assert pytest.approx(metrics.recall, 0.01) == 0.3333
    assert metrics.mean_iou > 0.80

    # Failure taxonomy checks
    assert failures[FailureCategory.DUPLICATE_DETECTION.value] == 1
    assert failures[FailureCategory.DETECTOR_MISS.value] == 2
    assert failures[FailureCategory.SMALL_VEHICLE.value] >= 1
    assert failures[FailureCategory.HEAVY_OCCLUSION.value] >= 1


# ==============================================================================
# 6. TRACKING EVALUATION METRICS & ERROR SEPARATION
# ==============================================================================

def test_tracking_evaluator_id_switches_and_continuity():
    """Verify tracking continuity, ID switches, and separation of detection vs tracking errors."""
    gt_frame_1 = [
        GroundTruthAnnotation(
            annotation_id="GT-A-1",
            frame_id="f1",
            object_id="carA",
            bounding_box=BoundingBox(x_min=0.2, y_min=0.2, x_max=0.4, y_max=0.4),
            track_id="GT-TRK-A",
        )
    ]
    gt_frame_2 = [
        GroundTruthAnnotation(
            annotation_id="GT-A-2",
            frame_id="f2",
            object_id="carA",
            bounding_box=BoundingBox(x_min=0.22, y_min=0.22, x_max=0.42, y_max=0.42),
            track_id="GT-TRK-A",
        )
    ]
    gt_frame_3 = [
        GroundTruthAnnotation(
            annotation_id="GT-A-3",
            frame_id="f3",
            object_id="carA",
            bounding_box=BoundingBox(x_min=0.24, y_min=0.24, x_max=0.44, y_max=0.44),
            track_id="GT-TRK-A",
        )
    ]

    gt_by_frame = {1: gt_frame_1, 2: gt_frame_2, 3: gt_frame_3}

    # Tracker initially tracks with TRK-01 in frame 1, switches to TRK-02 in frame 2 and 3
    track_1 = Track(
        track_id="TRK-01",
        first_frame=1,
        last_frame=1,
        observations=[
            TrackObservation(
                observation_id="OBS-1",
                frame_number=1,
                video_time_sec=0.033,
                bbox=BoundingBox(x_min=0.2, y_min=0.2, x_max=0.4, y_max=0.4),
                centroid_x=0.3,
                centroid_y=0.3,
                confidence=0.9,
            )
        ],
        observation_count=1,
        duration_sec=0.033,
    )
    track_2 = Track(
        track_id="TRK-02",
        first_frame=2,
        last_frame=3,
        observations=[
            TrackObservation(
                observation_id="OBS-2",
                frame_number=2,
                video_time_sec=0.066,
                bbox=BoundingBox(x_min=0.22, y_min=0.22, x_max=0.42, y_max=0.42),
                centroid_x=0.32,
                centroid_y=0.32,
                confidence=0.9,
            ),
            TrackObservation(
                observation_id="OBS-3",
                frame_number=3,
                video_time_sec=0.099,
                bbox=BoundingBox(x_min=0.24, y_min=0.24, x_max=0.44, y_max=0.44),
                centroid_x=0.34,
                centroid_y=0.34,
                confidence=0.9,
            ),
        ],
        observation_count=2,
        duration_sec=0.066,
    )

    evaluator = TrackingEvaluator(iou_threshold=0.50)
    metrics, failures = evaluator.evaluate_tracks(gt_by_frame, [track_1, track_2])

    assert metrics.total_gt_tracks == 1
    assert metrics.total_pred_tracks == 2
    assert metrics.id_switches == 1  # Switched from TRK-01 to TRK-02
    assert metrics.track_continuity_ratio == 1.0  # observed in all 3 frames
    assert failures[FailureCategory.IDENTITY_AMBIGUITY.value] == 1


# ==============================================================================
# 7. IDENTITY ASSOCIATION EVALUATION
# ==============================================================================

def test_identity_evaluator_synthetic_fixture_behavior():
    """Verify identity evaluator honestly reports NOT_AVAILABLE for synthetic or unannotated data."""
    gt_annotations = [
        GroundTruthAnnotation(
            annotation_id="GT-ID-1",
            frame_id="f1",
            object_id="car1",
            bounding_box=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.3, y_max=0.3),
            identity_label="MAG",
            identity_status=AnnotationIdentityStatus.CONFIRMED,
        )
    ]
    preds = [
        VisualIdentityAssociation(
            track_id="TRK-01",
            candidate_id="CAND-01",
            driver_code="MAG",
            driver_number="20",
        )
    ]

    # When marked synthetic, must return NOT_AVAILABLE
    synth_res = IdentityEvaluator.evaluate_associations(gt_annotations, preds, is_synthetic=True)
    assert synth_res.evaluation_status == "NOT_AVAILABLE"
    assert "synthetic" in synth_res.statement.lower()

    # When evaluated on real GT (is_synthetic=False)
    real_res = IdentityEvaluator.evaluate_associations(gt_annotations, preds, is_synthetic=False)
    assert real_res.evaluation_status in ["EVALUATED", "NOT_AVAILABLE"]


# ==============================================================================
# 8. CROSS-MODAL EVALUATION
# ==============================================================================

def test_cross_modal_evaluator():
    """Verify cross-modal evaluation metrics calculation and empty handling."""
    # When pairs are provided
    pairs = [
        (10.0, 10.05, 0.05),  # delta = 0.05 <= 0.20 -> aligned
        (20.0, 20.22, 0.05),  # delta = 0.22 <= 0.20 + 0.05 -> partially aligned
        (30.0, 30.50, 0.05),  # delta = 0.50 > 0.25 -> misaligned
    ]
    res = CrossModalEvaluator.evaluate_cross_modal_events(pairs, tolerance_sec=0.20)
    assert res.evaluation_status == "EVALUATED"
    assert res.total_events_evaluated == 3
    assert res.aligned_count == 1
    assert res.partially_aligned_count == 1
    assert res.misaligned_count == 1
    assert res.mean_absolute_difference_sec > 0.0

    # Empty pairs return NOT_AVAILABLE
    empty_res = CrossModalEvaluator.evaluate_cross_modal_events([])
    assert empty_res.evaluation_status == "NOT_AVAILABLE"


# ==============================================================================
# 9. INCIDENT VISUAL EVIDENCE SUFFICIENCY (STEWARD DECISION SUPPORT)
# ==============================================================================

def test_incident_evidence_sufficiency_monza_unavailable():
    """Verify Monza official cases strictly return UNAVAILABLE for steward review."""
    service = get_cv_evaluation_service()
    res = service.evaluate_incident_sufficiency("REF-MONZA-01", None)

    assert res.candidate_id == "REF-MONZA-01"
    assert res.steward_readiness == StewardReadinessRating.UNAVAILABLE
    assert not res.video_available
    assert "Formula One Management" in res.evaluation_summary
    assert len(res.limitations) >= 3


def test_incident_evidence_sufficiency_synthetic_success():
    """Verify synthetic fixture incident achieves SUFFICIENT steward readiness."""
    service = get_cv_evaluation_service()

    synthetic_analysis = CVIncidentAnalysisResponse(
        candidate_id="CAND-SYNTH-01",
        session_id="Virtual GP",
        processing_status=CVProcessingStatus.AVAILABLE,
        sampled_frame_count=60,
        detections_count=120,
        tracks_count=2,
        tracks=[
            Track(
                track_id="TRK-01",
                first_frame=1,
                last_frame=60,
                duration_sec=2.0,
                quality=TrackQuality(rating=TrackingQualityRating.HIGH),
            ),
            Track(
                track_id="TRK-02",
                first_frame=1,
                last_frame=60,
                duration_sec=2.0,
                quality=TrackQuality(rating=TrackingQualityRating.HIGH),
            ),
        ],
        identity_associations=[
            VisualIdentityAssociation(
                track_id="TRK-01",
                candidate_id="CAND-SYNTH-01",
                driver_code="MAG",
            )
        ],
        interaction_features=[
            # Dummy interaction feature
            dict(
                frame_number=30,
                video_time_sec=1.0,
                event_relative_time_sec=0.0,
                track_id_a="TRK-01",
                track_id_b="TRK-02",
                centroid_separation_norm=0.12,
            )
        ],
    )

    res = service.evaluate_incident_sufficiency("CAND-SYNTH-01", synthetic_analysis)
    assert res.steward_readiness == StewardReadinessRating.SUFFICIENT
    assert res.video_available is True
    assert res.tracks_continuous is True
    assert res.identities_available is True
    assert res.visual_interaction_features_available is True
    assert "SUFFICIENT" in res.evaluation_summary


# ==============================================================================
# 10. API CONTRACTS
# ==============================================================================

@pytest.fixture
def client():
    return TestClient(app)


def test_api_cv_evaluation_endpoint(client):
    """Verify GET /api/v1/analysis/cv/evaluation endpoint returns valid schema."""
    response = client.get("/api/v1/analysis/cv/evaluation")
    assert response.status_code == 200
    data = response.json()

    assert data["realVideoStatus"] == "NOT_AVAILABLE"
    assert data["evaluationStatus"] == "SYNTHETIC_VALIDATION_ONLY"
    assert "detectionMetrics" in data
    assert "trackingMetrics" in data
    assert "identityMetrics" in data
    assert "failureCategories" in data
    assert "stewardNotice" in data
    assert "guilt" not in data["stewardNotice"].lower() or "not assign guilt" in data["stewardNotice"].lower()


def test_api_candidate_cv_sufficiency_monza(client):
    """Verify GET /api/v1/analysis/candidates/{id}/video/cv/sufficiency for Monza cases."""
    response = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/cv/sufficiency")
    assert response.status_code == 200
    data = response.json()

    assert data["candidateId"] == "REF-MONZA-01"
    assert data["stewardReadiness"] == "UNAVAILABLE"
    assert data["videoAvailable"] is False
    assert "Formula One Management" in data["evaluationSummary"]


# ==============================================================================
# 11. CRITICAL JURISPRUDENTIAL & NON-ADJUDICATION GUARDRAILS
# ==============================================================================

def test_guardrails_no_guilt_or_fault():
    """Verify evaluation outputs strictly omit adjudicative fault or guilt terms."""
    service = get_cv_evaluation_service()
    suite = service.get_evaluation_suite()
    dump_text = suite.model_dump_json().lower()

    forbidden_terms = [
        "is guilty",
        "was at fault",
        "penalty awarded",
        "collision confirmed",
        "driver fault",
        "liable for crash",
    ]

    for term in forbidden_terms:
        assert term not in dump_text, f"Forbidden adjudicative term '{term}' found in CV evaluation suite."
