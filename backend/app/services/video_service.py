"""Video evidence service orchestrating multi-camera alignment, calibration transforms, and CV frame extraction.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS (PROMPT 12):
    1. Zero Copyright Infringement: Never packages or redistributes broadcast video footage.
    2. Honest VIDEO_UNAVAILABLE Default: If video bytes are unlinked, returns VIDEO_UNAVAILABLE honestly.
    3. Test Fixture Isolation: Synthetic calibration fixtures are strictly flagged as TEST_FIXTURE and never
       confused with real race footage.
    4. Orthogonal Multi-Modal Architecture: Video synchronization never alters or overwrites telemetry,
       baseline deviations, geometry, or ML pattern evidence.
"""

from typing import Any, Dict, List, Optional
from app.evidence.video_evidence import (
    AnchorEventType,
    CalibrationPoint,
    CameraAlignmentInfo,
    IncidentVideoWindow,
    SynchronizedVideoFrame,
    SyncConfidence,
    SyncMethod,
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


class VideoSynchronizationService:
    """Service providing multi-camera synchronization, affine time transforms, and incident clip boundaries."""

    def __init__(self):
        self._sources_registry: Dict[str, List[VideoSourceMetadata]] = {}
        self._initialize_reference_and_fixture_sources()

    def _initialize_reference_and_fixture_sources(self) -> None:
        """Register documented metadata for Monza 2024 reference cases and automated test fixtures."""
        
        # 1. MONZA 2024 OFFICIAL INCIDENTS (Metadata Only, Actual Video Honestly UNAVAILABLE)
        # ------------------------------------------------------------------------------
        monza_session_id = "f1-2024-italian grand prix-race"

        # REF-MONZA-01 (RIC vs HUL, Lap 1, Ascari)
        self._sources_registry["REF-MONZA-01"] = [
            VideoSourceMetadata(
                video_id="FOM-2024-ITA-WF-L01",
                source_type=VideoSourceType.BROADCAST.value,
                source_reference="FOM World Feed Broadcast Log - Lap 1 Ascari Sequence",
                session_id=monza_session_id,
                camera_label="World Feed Broadcast",
                sync_status=VideoSyncStatus.VIDEO_UNAVAILABLE,
                availability_status="UNAVAILABLE",
                license_note="Formula 1 World Championship broadcast rights belong to FOM. Video stream unlinked.",
                provenance=VideoProvenanceRecord(
                    source="Formula One Management (FOM)",
                    source_reference="FIA Document 54 / World Feed Ch.1",
                    acquisition_method="UNLINKED",
                    session="Italian Grand Prix 2024 — Race",
                    camera="World Feed Main",
                    timestamp_basis="FASTF1_TIME_OFFSET",
                    availability="VIDEO_UNAVAILABLE",
                    metadata_quality="UNVERIFIED",
                ),
            )
        ]

        # REF-MONZA-02 (HUL vs TSU, Lap 4, Prima Variante)
        self._sources_registry["REF-MONZA-02"] = [
            VideoSourceMetadata(
                video_id="FOM-2024-ITA-WF-L04",
                source_type=VideoSourceType.BROADCAST.value,
                source_reference="FOM World Feed Broadcast Log - Lap 4 Turn 1",
                session_id=monza_session_id,
                camera_label="World Feed Broadcast",
                sync_status=VideoSyncStatus.VIDEO_UNAVAILABLE,
                availability_status="UNAVAILABLE",
                provenance=VideoProvenanceRecord(
                    source="Formula One Management (FOM)",
                    source_reference="FIA Document 55",
                    acquisition_method="UNLINKED",
                    session="Italian Grand Prix 2024 — Race",
                    camera="World Feed Main",
                    timestamp_basis="FASTF1_TIME_OFFSET",
                    availability="VIDEO_UNAVAILABLE",
                    metadata_quality="UNVERIFIED",
                ),
            )
        ]

        # REF-MONZA-03 (MAG vs GAS, Lap 19, Roggia)
        self._sources_registry["REF-MONZA-03"] = [
            VideoSourceMetadata(
                video_id="FOM-2024-ITA-WF-L19",
                source_type=VideoSourceType.BROADCAST.value,
                source_reference="FOM World Feed Broadcast Log - Lap 19 Roggia",
                session_id=monza_session_id,
                camera_label="World Feed Broadcast",
                sync_status=VideoSyncStatus.VIDEO_UNAVAILABLE,
                availability_status="UNAVAILABLE",
                provenance=VideoProvenanceRecord(
                    source="Formula One Management (FOM)",
                    source_reference="FIA Document 58",
                    acquisition_method="UNLINKED",
                    session="Italian Grand Prix 2024 — Race",
                    camera="World Feed Main",
                    timestamp_basis="FASTF1_TIME_OFFSET",
                    availability="VIDEO_UNAVAILABLE",
                    metadata_quality="UNVERIFIED",
                ),
            )
        ]

        # 2. TEST FIXTURES (Explicitly Labeled TEST_FIXTURE for Automated Testing)
        # -----------------------------------------------------------------------
        fixture_session_id = "test-session-fixture-2024"

        # Multi-camera setup for TEST-CANDIDATE-01:
        # Camera A: World Feed (50 fps, constant offset +10s)
        # Camera B: Car 20 Onboard (25 fps, direct timecode)
        # Camera C: Turn 4 Trackside CCTV (30 fps, affine time drift test)
        cam_a_pts = [
            CalibrationPoint(
                point_id="PT-A1",
                name="Start/Finish Line Gantry Crossing",
                video_time_sec=10.0,
                session_time_sec=0.0,
                anchor_type=AnchorEventType.START_FINISH_CROSSING,
                description="Visual crossing of start line gantry in world feed",
            ),
            CalibrationPoint(
                point_id="PT-A2",
                name="Turn 1 Braking Board 100m",
                video_time_sec=25.0,
                session_time_sec=15.0,
                anchor_type=AnchorEventType.INCIDENT_TIMESTAMP,
                description="Car nose crosses 100m braking marker",
            ),
        ]
        cam_a_transform = compute_calibration_transform(cam_a_pts, method=SyncMethod.DIRECT_TIMESTAMP, nominal_frame_rate=50.0)

        cam_b_pts = [
            CalibrationPoint(
                point_id="PT-B1",
                name="Steering Wheel Dash Display Lap 1 Time",
                video_time_sec=0.0,
                session_time_sec=0.0,
                anchor_type=AnchorEventType.LIGHTS_OUT,
                description="Steering wheel lap timer trigger synchronized with ECU CAN-bus",
            )
        ]
        cam_b_transform = compute_calibration_transform(cam_b_pts, method=SyncMethod.DIRECT_TIMESTAMP, nominal_frame_rate=25.0)

        # Affine test: intentional slight scale drift (1.002) for stress testing
        cam_c_pts = [
            CalibrationPoint(
                point_id="PT-C1",
                name="T4 Apex Kerb Entry",
                video_time_sec=5.000,
                session_time_sec=0.000,
                anchor_type=AnchorEventType.INCIDENT_TIMESTAMP,
            ),
            CalibrationPoint(
                point_id="PT-C2",
                name="T4 Exit Kerb Crossing",
                video_time_sec=25.040,
                session_time_sec=20.000,
                anchor_type=AnchorEventType.CUSTOM,
            ),
        ]
        cam_c_transform = compute_calibration_transform(cam_c_pts, method=SyncMethod.EVENT_ANCHOR, nominal_frame_rate=30.0)

        self._sources_registry["TEST_FIXTURE"] = [
            VideoSourceMetadata(
                video_id="FIXTURE-CAM-WF",
                source_type=VideoSourceType.BROADCAST.value,
                source_url="/fixtures/test_world_feed.mp4",
                source_reference="Synthetic Test Fixture - World Feed",
                session_id=fixture_session_id,
                camera_label="Test Broadcast World Feed",
                duration_sec=3600.0,
                sync_status=VideoSyncStatus.VIDEO_SYNCHRONIZED,
                frame_rate=50.0,
                resolution="1920x1080",
                timezone="UTC",
                transform=cam_a_transform,
                calibration_points=cam_a_pts,
                availability_status="AVAILABLE",
                provenance=VideoProvenanceRecord(
                    source="Synthetic Test Engine",
                    source_reference="TEST_FIXTURE_RECORD",
                    acquisition_method="TEST_FIXTURE",
                    session=fixture_session_id,
                    camera="Test World Feed",
                    timestamp_basis="SMPTE_LTC",
                    availability="STREAM_AVAILABLE",
                    metadata_quality="HIGH",
                ),
            ),
            VideoSourceMetadata(
                video_id="FIXTURE-CAM-ONBOARD",
                source_type=VideoSourceType.ONBOARD.value,
                source_url="/fixtures/test_onboard_car20.mp4",
                source_reference="Synthetic Test Fixture - Car 20 Onboard",
                session_id=fixture_session_id,
                camera_label="Car 20 Onboard Roll-Hoop",
                duration_sec=3600.0,
                sync_status=VideoSyncStatus.VIDEO_SYNCHRONIZED,
                frame_rate=25.0,
                resolution="1920x1080",
                timezone="UTC",
                transform=cam_b_transform,
                calibration_points=cam_b_pts,
                availability_status="AVAILABLE",
                provenance=VideoProvenanceRecord(
                    source="Synthetic Test Engine",
                    source_reference="TEST_FIXTURE_RECORD",
                    acquisition_method="TEST_FIXTURE",
                    session=fixture_session_id,
                    camera="Car 20 Onboard",
                    timestamp_basis="NTP_UTC",
                    availability="STREAM_AVAILABLE",
                    metadata_quality="HIGH",
                ),
            ),
            VideoSourceMetadata(
                video_id="FIXTURE-CAM-TRACKSIDE",
                source_type=VideoSourceType.TRACKSIDE.value,
                source_url="/fixtures/test_trackside_t4.mp4",
                source_reference="Synthetic Test Fixture - Turn 4 CCTV",
                session_id=fixture_session_id,
                camera_label="Turn 4 Trackside High-Angle CCTV",
                duration_sec=3600.0,
                sync_status=VideoSyncStatus.VIDEO_SYNCHRONIZED,
                frame_rate=30.0,
                resolution="1280x720",
                timezone="UTC",
                transform=cam_c_transform,
                calibration_points=cam_c_pts,
                availability_status="AVAILABLE",
                provenance=VideoProvenanceRecord(
                    source="Synthetic Test Engine",
                    source_reference="TEST_FIXTURE_RECORD",
                    acquisition_method="TEST_FIXTURE",
                    session=fixture_session_id,
                    camera="Turn 4 CCTV",
                    timestamp_basis="SESSION_ELAPSED",
                    availability="STREAM_AVAILABLE",
                    metadata_quality="NOMINAL",
                ),
            ),
        ]

    def get_sources_for_candidate(self, candidate_id: str) -> List[VideoSourceMetadata]:
        """Retrieve registered video sources for a candidate or return empty list if unlinked."""
        if candidate_id in self._sources_registry:
            return self._sources_registry[candidate_id]
        
        # Check if candidate_id is a test fixture request
        if "FIXTURE" in candidate_id.upper() or "TEST" in candidate_id.upper():
            return self._sources_registry.get("TEST_FIXTURE", [])

        return []

    def build_video_evidence_for_candidate(
        self,
        candidate_id: str,
        session_id: str,
        event_start_str: str,
        event_peak_str: str,
        event_end_str: str,
        selected_source: Optional[VideoSourceMetadata] = None,
        pre_roll_sec: float = 5.0,
        post_roll_sec: float = 5.0,
    ) -> VideoEvidenceSummary:
        """Construct multi-camera video evidence dossier for a specific candidate."""
        sources = self.get_sources_for_candidate(candidate_id)
        
        if not sources and selected_source is None:
            # Honestly unavailable
            return build_video_evidence(
                session_id=session_id,
                event_start_str=event_start_str,
                event_peak_str=event_peak_str,
                event_end_str=event_end_str,
                source=None,
                pre_roll_sec=pre_roll_sec,
                post_roll_sec=post_roll_sec,
            )

        active_source = selected_source or sources[0]
        return build_video_evidence(
            session_id=session_id,
            event_start_str=event_start_str,
            event_peak_str=event_peak_str,
            event_end_str=event_end_str,
            source=active_source,
            pre_roll_sec=pre_roll_sec,
            post_roll_sec=post_roll_sec,
            all_sources=sources,
        )

    def extract_synchronized_frame(
        self,
        source: VideoSourceMetadata,
        session_time_sec: float,
        session_timestamp_str: str = "",
    ) -> SynchronizedVideoFrame:
        """Extract a frame-accurate SynchronizedVideoFrame conforming to the Prompt 13 CV contract."""
        transform = source.transform or VideoTimeTransform(time_scale=1.0, offset_sec=0.0)
        v_sec = transform.session_to_video_time(session_time_sec)
        frame_num = transform.session_to_frame_number(session_time_sec, source.frame_rate)
        err = transform.uncertainty.estimated_error_seconds or 0.0

        return SynchronizedVideoFrame(
            video_id=source.video_id,
            camera=source.camera_label,
            video_timestamp=format_seconds_to_time(v_sec),
            video_time_sec=v_sec,
            session_timestamp=session_timestamp_str or format_seconds_to_time(session_time_sec),
            session_time_sec=session_time_sec,
            frame_number=frame_num,
            synchronization_error_sec=err,
            provenance=source.provenance,
        )


_video_service_instance: Optional[VideoSynchronizationService] = None


def get_video_service() -> VideoSynchronizationService:
    """Singleton accessor for VideoSynchronizationService."""
    global _video_service_instance
    if _video_service_instance is None:
        _video_service_instance = VideoSynchronizationService()
    return _video_service_instance
