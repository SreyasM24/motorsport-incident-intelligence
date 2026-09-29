"""Unit and integration test suite for Computer Vision Vehicle Detection, Tracking & Visual Identity Evidence (Prompt 14).

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS:
    1. Zero Autonomous Guilt or Fault Determination: Visual detections, tracks, and interaction features
       must NEVER assert fault, blame, legality, penalty, or collision contact verdicts.
    2. Zero Copyright Infringement & Zero Video Fabrication: Does NOT fabricate real race video.
       Real Grand Prix sessions without licensed footage (e.g. Monza reference cases) honestly return VIDEO_UNAVAILABLE.
    3. Model Decoupling & Honest Weight Status: Unconfigured or absent models honestly report MODEL_UNAVAILABLE;
       never auto-download external weights during tests.
    4. Evaluation Accuracy Honesty: Honest EVALUATION_STATUS: NOT_YET_AVAILABLE report. No fabricated real-world mAP.
    5. Bounded 2D Perspective Projection: All 2D image measurements carry measurement_basis = BOUNDED_2D_PROJECTION.
    6. Non-Adjudicative Language: Disallows "guilty", "at fault", "penalty applied", or "collision confirmed".
"""

import math
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.evidence.cv.contracts import (
    BoundingBox,
    CVEvaluationReport,
    CVEvaluationStatus,
    CVIncidentAnalysisResponse,
    CVPerformanceMetrics,
    CVProcessingStatus,
    Detection,
    DetectionFrame,
    IdentityMethod,
    ModelStatus,
    Track,
    TrackInteractionFeature,
    TrackObservation,
    TrackQuality,
    TrackerResult,
    TrackingQualityRating,
    VisualIdentityAssociation,
)
from app.evidence.cv.detector import (
    ConfigurableONNXVehicleDetector,
    NullVehicleDetector,
    SyntheticFixtureVehicleDetector,
    VehicleDetector,
)
from app.evidence.cv.tracker import (
    DeterministicSortTracker,
    VehicleTracker,
)
from app.evidence.cv.identity import VisualIdentityAssociator
from app.evidence.cv.features import compute_track_interaction_features
from app.evidence.cv.service import (
    CVIncidentService,
    get_cv_incident_service,
)
from app.evidence.visual.models import (
    AlignmentStatus,
    ApproachTrend,
    DriverAssociationStatus,
    VisibilityState,
)
from app.schemas.video_evidence import VideoProvenanceRecord


# ==============================================================================
# 1. BOUNDING BOX & GEOMETRIC MATH TESTS
# ==============================================================================

class TestBoundingBoxContracts:
    """Test 2D normalized bounding box geometry and distance operations."""

    def test_bounding_box_valid_initialization(self):
        bbox = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.5, y_max=0.6)
        assert bbox.x_min == 0.1
        assert bbox.y_min == 0.2
        assert bbox.x_max == 0.5
        assert bbox.y_max == 0.6
        assert math.isclose(bbox.width, 0.4)
        assert math.isclose(bbox.height, 0.4)
        assert math.isclose(bbox.area, 0.16)
        assert bbox.centroid == (0.3, 0.4)

    def test_bounding_box_invalid_range_raises_validation_error(self):
        with pytest.raises(Exception):
            BoundingBox(x_min=-0.1, y_min=0.2, x_max=0.5, y_max=0.6)
        with pytest.raises(Exception):
            BoundingBox(x_min=0.1, y_min=0.2, x_max=1.5, y_max=0.6)

    def test_bounding_box_identical_iou(self):
        b1 = BoundingBox(x_min=0.2, y_min=0.2, x_max=0.6, y_max=0.6)
        b2 = BoundingBox(x_min=0.2, y_min=0.2, x_max=0.6, y_max=0.6)
        iou = b1.compute_iou(b2)
        assert math.isclose(iou, 1.0, abs_tol=1e-4)

    def test_bounding_box_disjoint_iou(self):
        b1 = BoundingBox(x_min=0.0, y_min=0.0, x_max=0.2, y_max=0.2)
        b2 = BoundingBox(x_min=0.5, y_min=0.5, x_max=0.7, y_max=0.7)
        assert b1.compute_iou(b2) == 0.0

    def test_bounding_box_partial_overlap_iou(self):
        # b1: [0.0, 0.0, 0.4, 0.4] -> area = 0.16
        # b2: [0.2, 0.2, 0.6, 0.6] -> area = 0.16
        # intersection: [0.2, 0.2, 0.4, 0.4] -> area = 0.2 * 0.2 = 0.04
        # union: 0.16 + 0.16 - 0.04 = 0.28
        # IoU = 0.04 / 0.28 = 0.142857 -> round to 0.1429
        b1 = BoundingBox(x_min=0.0, y_min=0.0, x_max=0.4, y_max=0.4)
        b2 = BoundingBox(x_min=0.2, y_min=0.2, x_max=0.6, y_max=0.6)
        iou = b1.compute_iou(b2)
        assert abs(iou - 0.1429) < 0.001

    def test_bounding_box_centroid_distance(self):
        b1 = BoundingBox(x_min=0.0, y_min=0.0, x_max=0.2, y_max=0.2)  # c1 = (0.1, 0.1)
        b2 = BoundingBox(x_min=0.3, y_min=0.4, x_max=0.5, y_max=0.6)  # c2 = (0.4, 0.5)
        # dx = 0.3, dy = 0.4 -> dist = sqrt(0.09 + 0.16) = 0.5
        dist = b1.centroid_distance(b2)
        assert math.isclose(dist, 0.5, abs_tol=1e-4)


# ==============================================================================
# 2. DETECTOR ABSTRACTION & STATUS TRANSPARENCY TESTS
# ==============================================================================

class TestVehicleDetectorImplementations:
    """Test vehicle detector abstraction and honest availability status reporting."""

    def test_null_vehicle_detector_returns_model_unavailable(self):
        detector = NullVehicleDetector()
        assert detector.get_model_status() == ModelStatus.MODEL_UNAVAILABLE
        detections = detector.detect(None)
        assert detections == []
        meta = detector.get_metadata()
        assert meta["model_name"] == "NullVehicleDetector"
        assert meta["status"] == ModelStatus.MODEL_UNAVAILABLE

    def test_configurable_onnx_detector_absent_path_defaults_to_model_unavailable(self):
        # Must not raise an exception or attempt external HTTP downloads
        detector = ConfigurableONNXVehicleDetector(model_path="non_existent_weights.onnx")
        assert detector.get_model_status() == ModelStatus.MODEL_UNAVAILABLE
        detections = detector.detect(None)
        assert detections == []

    def test_synthetic_fixture_detector_emits_deterministic_detections(self):
        detector = SyntheticFixtureVehicleDetector(confidence_a=0.95, confidence_b=0.91)
        assert detector.get_model_status() == ModelStatus.LOADED

        detections = detector.detect(None, relative_time_sec=0.0)
        assert len(detections) == 2
        assert detections[0].class_name == "vehicle"
        assert detections[1].class_name == "vehicle"
        assert detections[0].confidence == 0.95
        assert detections[1].confidence == 0.91

        # Check bounds
        for det in detections:
            assert 0.0 <= det.bbox.x_min <= 1.0
            assert 0.0 <= det.bbox.x_max <= 1.0
            assert 0.0 <= det.bbox.y_min <= 1.0
            assert 0.0 <= det.bbox.y_max <= 1.0


# ==============================================================================
# 3. DETERMINISTIC SORT TRACKER & QUALITY QUANTIFICATION TESTS
# ==============================================================================

class TestVehicleTracker:
    """Test deterministic multi-object tracking, coasting, and quality rating."""

    def test_tracker_initializes_and_creates_tracks(self):
        tracker = DeterministicSortTracker()
        det1 = Detection(
            detection_id="det-1",
            bbox=BoundingBox(x_min=0.2, y_min=0.4, x_max=0.4, y_max=0.6),
            confidence=0.92,
        )
        det2 = Detection(
            detection_id="det-2",
            bbox=BoundingBox(x_min=0.6, y_min=0.4, x_max=0.8, y_max=0.6),
            confidence=0.88,
        )
        frame0 = DetectionFrame(
            frame_number=0,
            video_id="vid-01",
            camera_id="cam-01",
            video_timestamp="00:00:05.000",
            video_time_sec=5.0,
            detections=[det1, det2],
        )

        active = tracker.update(frame0)
        assert len(active) == 2
        assert tracker.get_result().total_tracks == 2
        assert active[0].track_id == "TRK-01"
        assert active[1].track_id == "TRK-02"

    def test_tracker_continuation_and_association(self):
        tracker = DeterministicSortTracker()

        # Frame 0
        f0 = DetectionFrame(
            frame_number=0,
            video_id="vid-01",
            camera_id="cam-01",
            video_timestamp="00:00:05.000",
            video_time_sec=5.0,
            detections=[
                Detection(
                    detection_id="det-0-1",
                    bbox=BoundingBox(x_min=0.30, y_min=0.40, x_max=0.45, y_max=0.55),
                    confidence=0.95,
                )
            ],
        )
        tracker.update(f0)

        # Frame 1: Small displacement, high IoU
        f1 = DetectionFrame(
            frame_number=1,
            video_id="vid-01",
            camera_id="cam-01",
            video_timestamp="00:00:05.040",
            video_time_sec=5.04,
            detections=[
                Detection(
                    detection_id="det-1-1",
                    bbox=BoundingBox(x_min=0.31, y_min=0.41, x_max=0.46, y_max=0.56),
                    confidence=0.94,
                )
            ],
        )
        active1 = tracker.update(f1)
        assert len(active1) == 1
        assert active1[0].track_id == "TRK-01"
        assert active1[0].observation_count == 2

    def test_tracker_coasting_and_termination(self):
        # Max age = 2 frames
        tracker = DeterministicSortTracker(max_age=2, min_hits=1)

        # Frame 0: detection present
        tracker.update(
            DetectionFrame(
                frame_number=0,
                video_id="vid-01",
                camera_id="cam-01",
                video_timestamp="00:00:05.000",
                video_time_sec=5.0,
                detections=[
                    Detection(
                        detection_id="det-0",
                        bbox=BoundingBox(x_min=0.4, y_min=0.4, x_max=0.5, y_max=0.5),
                        confidence=0.9,
                    )
                ],
            )
        )
        assert len(tracker.get_tracks(active_only=True)) == 1

        # Frame 1: missed detection (coast 1)
        tracker.update(
            DetectionFrame(
                frame_number=1,
                video_id="vid-01",
                camera_id="cam-01",
                video_timestamp="00:00:05.040",
                video_time_sec=5.04,
                detections=[],
            )
        )
        assert len(tracker.get_tracks(active_only=True)) == 1
        assert tracker.get_tracks()[0].observations[-1].is_interpolated is True

        # Frame 2: missed detection (coast 2, max_age reached)
        tracker.update(
            DetectionFrame(
                frame_number=2,
                video_id="vid-01",
                camera_id="cam-01",
                video_timestamp="00:00:05.080",
                video_time_sec=5.08,
                detections=[],
            )
        )

        # Frame 3: exceeds max_age -> track terminates
        tracker.update(
            DetectionFrame(
                frame_number=3,
                video_id="vid-01",
                camera_id="cam-01",
                video_timestamp="00:00:05.120",
                video_time_sec=5.12,
                detections=[],
            )
        )
        result = tracker.get_result()
        assert len(result.active_tracks) == 0
        assert len(result.terminated_tracks) == 1
        assert result.terminated_tracks[0].is_active is False

    def test_tracker_reset_clears_state(self):
        tracker = DeterministicSortTracker()
        tracker.update(
            DetectionFrame(
                frame_number=0,
                video_id="vid-01",
                camera_id="cam-01",
                video_timestamp="00:00:05.000",
                video_time_sec=5.0,
                detections=[
                    Detection(
                        detection_id="det-0",
                        bbox=BoundingBox(x_min=0.2, y_min=0.2, x_max=0.3, y_max=0.3),
                        confidence=0.85,
                    )
                ],
            )
        )
        assert tracker.get_result().total_tracks == 1
        tracker.reset()
        assert tracker.get_result().total_tracks == 0
        assert len(tracker.get_tracks()) == 0

    def test_track_quality_deterministic_classification(self):
        tracker = DeterministicSortTracker()
        # Feed 25 consecutive high-confidence frames -> rating should be HIGH
        for f in range(25):
            tracker.update(
                DetectionFrame(
                    frame_number=f,
                    video_id="vid-01",
                    camera_id="cam-01",
                    video_timestamp=f"00:00:0{5 + f * 0.04:.3f}",
                    video_time_sec=5.0 + f * 0.04,
                    detections=[
                        Detection(
                            detection_id=f"det-{f}",
                            bbox=BoundingBox(x_min=0.4, y_min=0.4, x_max=0.5, y_max=0.5),
                            confidence=0.92,
                        )
                    ],
                )
            )

        track = tracker.get_tracks()[0]
        assert track.quality.rating == TrackingQualityRating.HIGH
        assert track.quality.observation_count == 25
        assert track.quality.visibility_ratio >= 0.95
        assert track.quality.mean_confidence >= 0.85

    def test_tracker_never_assigns_driver_identity(self):
        """Guardrail: Tracker must emit geometric tracks only, NEVER assigning driver code or fault."""
        tracker = DeterministicSortTracker()
        tracker.update(
            DetectionFrame(
                frame_number=0,
                video_id="vid-01",
                camera_id="cam-01",
                video_timestamp="00:00:05.000",
                video_time_sec=5.0,
                detections=[
                    Detection(
                        detection_id="det-0",
                        bbox=BoundingBox(x_min=0.2, y_min=0.2, x_max=0.4, y_max=0.4),
                        confidence=0.9,
                    )
                ],
            )
        )
        track = tracker.get_tracks()[0]
        # Must be None until explicitly evaluated by VisualIdentityAssociator
        assert track.identity_association is None


# ==============================================================================
# 4. VISUAL IDENTITY ASSOCIATION TESTS
# ==============================================================================

class TestVisualIdentityAssociator:
    """Test defensible identity association and rejection of naive heuristics."""

    def test_associator_rejects_empty_tracks(self):
        associator = VisualIdentityAssociator()
        associations = associator.associate_identities([], "INC-001")
        assert associations == []

    def test_fixed_onboard_camera_associates_lead_driver_confirmed(self):
        associator = VisualIdentityAssociator()
        track1 = Track(track_id="TRK-01", first_frame=0, last_frame=10, observation_count=10)
        track2 = Track(track_id="TRK-02", first_frame=0, last_frame=10, observation_count=10)

        prov = VideoProvenanceRecord(
            source="FOM",
            source_reference="CAM_ONBOARD_MAG",
            acquisition_method="BROADCAST",
            session="MONZA_2024",
            camera="CAR 20 NOSE",
            timestamp_basis="UTC",
            availability="AVAILABLE",
            metadata_quality="HIGH",
        )

        associations = associator.associate_identities(
            tracks=[track1, track2],
            candidate_id="INC-MAG-HUL",
            driver_a_code="MAG",
            driver_a_number="20",
            driver_b_code="HUL",
            driver_b_number="27",
            provenance=prov,
        )

        assert len(associations) == 2
        assoc1 = next(a for a in associations if a.track_id == "TRK-01")
        assert assoc1.driver_code == "MAG"
        assert assoc1.association_status == DriverAssociationStatus.CONFIRMED
        assert assoc1.method == IdentityMethod.ONBOARD_CAMERA_FIXED

        assoc2 = next(a for a in associations if a.track_id == "TRK-02")
        assert assoc2.driver_code == "HUL"
        assert assoc2.association_status == DriverAssociationStatus.INFERRED

    def test_telemetry_track_order_without_fixed_camera_inferred(self):
        associator = VisualIdentityAssociator()
        track1 = Track(track_id="TRK-01", first_frame=0, last_frame=10, observation_count=10)

        associations = associator.associate_identities(
            tracks=[track1],
            candidate_id="INC-01",
            driver_a_code="VER",
            driver_a_number="1",
            provenance=None,
        )

        assert len(associations) == 1
        assert associations[0].driver_code == "VER"
        assert associations[0].association_status == DriverAssociationStatus.INFERRED
        assert associations[0].method == IdentityMethod.TELEMETRY_TRACK_ORDER

    def test_unassociated_when_no_driver_metadata_available(self):
        associator = VisualIdentityAssociator()
        track1 = Track(track_id="TRK-01", first_frame=0, last_frame=5, observation_count=5)

        associations = associator.associate_identities(
            tracks=[track1],
            candidate_id="INC-UNKNOWN",
            driver_a_code=None,
        )

        assert len(associations) == 1
        assert associations[0].association_status == DriverAssociationStatus.UNAVAILABLE
        assert associations[0].method == IdentityMethod.UNASSOCIATED


# ==============================================================================
# 5. PAIRWISE VISUAL INTERACTION FEATURES TESTS
# ==============================================================================

class TestTrackInteractionFeatures:
    """Test pairwise geometric interaction quantification between tracks."""

    def test_interaction_features_computed_with_bounded_2d_projection(self):
        # Create two tracks approaching each other
        obs_a = [
            TrackObservation(
                observation_id=f"obs-a-{i}",
                frame_number=i,
                video_time_sec=5.0 + i * 0.04,
                bbox=BoundingBox(x_min=0.2 + i * 0.01, y_min=0.4, x_max=0.3 + i * 0.01, y_max=0.6),
                centroid_x=0.25 + i * 0.01,
                centroid_y=0.5,
                confidence=0.9,
            )
            for i in range(5)
        ]
        obs_b = [
            TrackObservation(
                observation_id=f"obs-b-{i}",
                frame_number=i,
                video_time_sec=5.0 + i * 0.04,
                bbox=BoundingBox(x_min=0.7 - i * 0.01, y_min=0.4, x_max=0.8 - i * 0.01, y_max=0.6),
                centroid_x=0.75 - i * 0.01,
                centroid_y=0.5,
                confidence=0.9,
            )
            for i in range(5)
        ]

        track_a = Track(track_id="TRK-01", first_frame=0, last_frame=4, observations=obs_a, observation_count=5)
        track_b = Track(track_id="TRK-02", first_frame=0, last_frame=4, observations=obs_b, observation_count=5)

        features = compute_track_interaction_features(track_a, track_b, peak_video_time_sec=5.08)

        assert len(features) == 5
        # Guardrail: measurement basis must be BOUNDED_2D_PROJECTION
        for f in features:
            assert f.measurement_basis == "BOUNDED_2D_PROJECTION"
            assert f.track_id_a == "TRK-01"
            assert f.track_id_b == "TRK-02"

        # Centroid distance should decrease over time (approaching)
        assert features[0].centroid_separation_norm > features[-1].centroid_separation_norm
        assert features[-1].approach_recede_trend == ApproachTrend.APPROACHING


# ==============================================================================
# 6. INCIDENT WINDOW CV SERVICE & REFERENCE CASE COMPLIANCE TESTS
# ==============================================================================

class TestCVIncidentService:
    """Test incident window scoping, evaluation transparency, and reference case guardrails."""

    def test_monza_reference_cases_honestly_return_video_unavailable(self):
        """Monza 2024 official sessions have no bundled licensed video; must report VIDEO_UNAVAILABLE."""
        service = CVIncidentService()
        for ref_id in ["REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"]:
            resp = service.analyze_incident_window(
                candidate_id=ref_id,
                session_id="monza_2024_race",
            )
            assert resp.processing_status == CVProcessingStatus.VIDEO_UNAVAILABLE
            assert resp.detections_count == 0
            assert resp.tracks_count == 0
            assert "unlinked" in resp.statement.lower() or "video_unavailable" in resp.statement.lower()

    def test_unconfigured_model_honestly_reports_model_unavailable(self):
        # Service configured with NullVehicleDetector
        service = CVIncidentService(detector=NullVehicleDetector())
        resp = service.analyze_incident_window(
            candidate_id="INC-SYNTH-01",
            session_id="test_session",
            has_video=True,
        )
        assert resp.processing_status == CVProcessingStatus.MODEL_UNAVAILABLE
        assert resp.model_status == ModelStatus.MODEL_UNAVAILABLE

    def test_synthetic_fixture_analysis_completes_available(self):
        service = CVIncidentService()
        resp = service.analyze_incident_window(
            candidate_id="INC-FIXTURE-01",
            session_id="test_fixture_session",
            peak_timestamp_str="13:42:18.4",
            driver_a_code="MAG",
            driver_a_number="20",
            driver_b_code="HUL",
            driver_b_number="27",
            has_video=True,
        )
        assert resp.processing_status == CVProcessingStatus.AVAILABLE
        assert resp.model_status == ModelStatus.LOADED
        assert resp.tracks_count >= 2
        assert len(resp.identity_associations) >= 2
        assert len(resp.interaction_features) > 0
        assert resp.performance is not None
        assert resp.performance.processed_frames > 0

    def test_evaluation_report_honesty(self):
        """Guardrail: Accuracy must report NOT_YET_AVAILABLE or SYNTHETIC_BENCHMARK_ONLY, never fabricating REAL_WORLD_EVALUATED."""
        service = CVIncidentService()
        # 1. Unlinked candidate -> NOT_YET_AVAILABLE
        resp_unlinked = service.analyze_incident_window(
            candidate_id="INC-REAL-02",
            session_id="test_broadcast_session",
            has_video=False,
        )
        assert resp_unlinked.evaluation.evaluation_status == CVEvaluationStatus.NOT_YET_AVAILABLE
        assert "not_yet_available" in resp_unlinked.evaluation.statement.lower()

        # 2. Fixture candidate -> SYNTHETIC_BENCHMARK_ONLY
        resp_fixture = service.analyze_incident_window(
            candidate_id="INC-FIXTURE-02",
            session_id="test_fixture_session",
            has_video=True,
        )
        assert resp_fixture.evaluation.evaluation_status == CVEvaluationStatus.SYNTHETIC_BENCHMARK_ONLY
        assert resp_fixture.evaluation.evaluation_status != CVEvaluationStatus.REAL_WORLD_EVALUATED


# ==============================================================================
# 7. FASTAPI API INTEGRATION TESTS
# ==============================================================================

class TestCVAPIIntegration:
    """Test HTTP endpoint GET /api/v1/analysis/candidates/{candidate_id}/video/cv."""

    def test_api_cv_analysis_returns_valid_schema(self):
        client = TestClient(app)
        res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/cv")
        assert res.status_code == 200
        data = res.json()

        assert "candidateId" in data or "candidate_id" in data
        assert "processingStatus" in data or "processing_status" in data
        assert "tracks" in data
        assert "identityAssociations" in data or "identity_associations" in data
        assert "interactionFeatures" in data or "interaction_features" in data
        assert "evaluation" in data

    def test_api_cv_analysis_monza_case_video_unavailable(self):
        client = TestClient(app)
        res = client.get("/api/v1/analysis/candidates/REF-MONZA-01/video/cv")
        assert res.status_code == 200
        data = res.json()
        status = data.get("processingStatus") or data.get("processing_status")
        assert status == "VIDEO_UNAVAILABLE"

    def test_api_cv_analysis_not_found(self):
        client = TestClient(app)
        res = client.get("/api/v1/analysis/candidates/NON_EXISTENT_CANDIDATE/video/cv")
        assert res.status_code == 404


# ==============================================================================
# 8. JURISPRUDENTIAL & COMPLIANCE GUARDRAILS AUDIT
# ==============================================================================

class TestCVGuardrailsCompliance:
    """Rigorous audit asserting absolute absence of guilt, fault, or penalties in CV layer."""

    FORBIDDEN_WORDS = [
        "guilty",
        "at fault",
        "driver fault",
        "penalty applied",
        "illegal move",
        "collision confirmed",
        "driver blameworthy",
    ]

    def test_no_adjudicative_language_in_service_output(self):
        service = CVIncidentService()
        resp = service.analyze_incident_window(
            candidate_id="INC-AUDIT-01",
            session_id="test_session",
            has_video=True,
        )
        serialized_json = resp.model_dump_json().lower()
        for forbidden in self.FORBIDDEN_WORDS:
            assert forbidden not in serialized_json, f"Forbidden adjudicative phrase '{forbidden}' found in CV output!"

    def test_measurement_basis_strictly_bounded(self):
        service = CVIncidentService()
        resp = service.analyze_incident_window(
            candidate_id="INC-AUDIT-02",
            session_id="test_session",
            has_video=True,
        )
        for feature in resp.interaction_features:
            assert feature.measurement_basis == "BOUNDED_2D_PROJECTION"
