"""Visual Evidence Service orchestrating keyframe extraction, 2D feature synthesis, and multi-modal alignment.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS (PROMPT 13):
    1. Zero Copyright Infringement: Never stores, streams, or distributes copyrighted FOM/FIA footage.
    2. Zero Hallucination: Monza 2024 reference cases honestly default to UNAVAILABLE.
    3. Test Fixture Isolation: Synthetic fixture evidence is strictly tagged with TEST_FIXTURE provenance.
    4. Orthogonal Decision Support: Visual features provide spatial corroboration; they NEVER decide guilt,
       penalties, or contact events.
"""

from typing import List, Optional

from app.evidence.video_evidence import (
    VideoSourceMetadata,
    VideoSyncStatus,
    parse_timestamp_to_seconds,
)
from app.evidence.visual.extractor import (
    VisualKeyframeExtractor,
    compute_cross_modal_alignment,
)
from app.evidence.visual.models import (
    AlignmentStatus,
    CrossModalAlignment,
    VisualEvidenceQuality,
    VisualEvidenceQualityRating,
    VisualEvidenceSummary,
    VisualObservationStatus,
)
from app.services.video_service import get_video_service


class VisualEvidenceService:
    """Service providing bounded visual evidence extraction, cross-modal checks, and quality assessment."""

    def __init__(self):
        self._extractor = VisualKeyframeExtractor()

    def build_visual_evidence_for_candidate(
        self,
        candidate_id: str,
        session_id: str,
        event_start_str: str,
        event_peak_str: str,
        event_end_str: str,
        driver_a: Optional[str] = "20",
        driver_b: Optional[str] = "27",
        selected_source: Optional[VideoSourceMetadata] = None,
        telemetry_peak_sec: Optional[float] = None,
    ) -> VisualEvidenceSummary:
        """Construct a complete VisualEvidenceSummary for a given candidate incident.
        
        Args:
            candidate_id: Unique candidate identifier.
            session_id: Racing session identifier.
            event_start_str: Event start timestamp string.
            event_peak_str: Event peak proximity / apex timestamp string.
            event_end_str: Event end timestamp string.
            driver_a: Primary driver number/identifier.
            driver_b: Secondary driver number/identifier.
            selected_source: Explicit video source to use (optional).
            telemetry_peak_sec: Session elapsed time of telemetry peak (optional).
            
        Returns:
            VisualEvidenceSummary ready for inclusion in the Incident Evidence Dossier.
        """
        t_peak_sec = (
            telemetry_peak_sec
            if telemetry_peak_sec is not None
            else parse_timestamp_to_seconds(event_peak_str)
        )

        # ----------------------------------------------------------------------
        # 1. HONEST UNAVAILABLE FOR MONZA 2024 OFFICIAL INCIDENTS
        # ----------------------------------------------------------------------
        monza_reference_ids = {"REF-MONZA-01", "REF-MONZA-02", "REF-MONZA-03"}
        clean_cid = (candidate_id or "").upper()
        clean_sid = (session_id or "").upper()
        is_official_monza = (
            candidate_id in monza_reference_ids
            or "MONZA" in clean_cid
            or "MON" in clean_cid
            or "ITA" in clean_cid
            or "ITALIAN" in clean_sid
            or "MONZA" in clean_sid
        ) and "FIXTURE" not in clean_cid and "TEST" not in clean_cid

        if is_official_monza:
            return VisualEvidenceSummary(
                status=VisualObservationStatus.UNAVAILABLE,
                camera_id=None,
                camera_label=None,
                keyframes=[],
                track_observations=[],
                cross_modal_alignment=CrossModalAlignment(
                    telemetry_event_time_sec=round(t_peak_sec, 3),
                    visual_event_time_sec=None,
                    delta_seconds=None,
                    synchronization_uncertainty_sec=0.0,
                    tolerance_sec=0.20,
                    alignment_status=AlignmentStatus.INSUFFICIENT_DATA,
                    description="Official race broadcast footage unlinked due to commercial licensing. Cross-modal visual alignment cannot be evaluated.",
                ),
                quality=VisualEvidenceQuality(
                    quality_rating=VisualEvidenceQualityRating.UNUSABLE,
                    notes=["Video footage unlinked; zero visual frames ingested."],
                ),
                statement=(
                    f"Visual evidence is unavailable and unlinked for candidate '{candidate_id}' in official session "
                    f"'{session_id}'. Formula One Management broadcast footage is protected under commercial copyright. "
                    f"Missing visual evidence is treated as an honest unobserved state, not negative evidence."
                ),
                limitations=[
                    "Broadcast footage unlinked; zero visual frames ingested.",
                    "No visual ROIs, bounding boxes, or image-plane features derived.",
                    "Incident evidence relies exclusively on telemetry, spatial baseline, and race control records.",
                ],
            )

        # ----------------------------------------------------------------------
        # 2. SOURCE RETRIEVAL & AVAILABILITY CHECK
        # ----------------------------------------------------------------------
        sources = get_video_service().get_sources_for_candidate(candidate_id)
        active_source = selected_source or (sources[0] if sources else None)

        if not active_source or active_source.sync_status == VideoSyncStatus.VIDEO_UNAVAILABLE:
            return VisualEvidenceSummary(
                status=VisualObservationStatus.UNAVAILABLE,
                camera_id=active_source.video_id if active_source else None,
                camera_label=active_source.camera_label if active_source else None,
                keyframes=[],
                track_observations=[],
                cross_modal_alignment=CrossModalAlignment(
                    telemetry_event_time_sec=round(t_peak_sec, 3),
                    visual_event_time_sec=None,
                    delta_seconds=None,
                    alignment_status=AlignmentStatus.INSUFFICIENT_DATA,
                    description="No synchronized visual stream available for cross-modal alignment.",
                ),
                quality=VisualEvidenceQuality(
                    quality_rating=VisualEvidenceQualityRating.UNUSABLE,
                    notes=["No synchronized video stream available."],
                ),
                statement="No verified visual broadcast footage is synchronized for this candidate event.",
                limitations=["Visual evidence unavailable."],
            )

        # ----------------------------------------------------------------------
        # 3. BOUNDED KEYFRAME & FEATURE EXTRACTION
        # ----------------------------------------------------------------------
        keyframes = self._extractor.extract_keyframes(
            source=active_source,
            event_peak_sec=t_peak_sec,
            driver_a=driver_a,
            driver_b=driver_b,
        )

        # Aggregate unique track observations
        track_obs_map = {}
        for kf in keyframes:
            for obs in kf.observations:
                if obs.track_id not in track_obs_map:
                    track_obs_map[obs.track_id] = obs
        track_obs_list = list(track_obs_map.values())

        # Cross-modal alignment check
        sync_err = (
            active_source.transform.uncertainty.estimated_error_seconds
            if active_source.transform
            else 0.0
        ) or 0.0
        cross_modal = compute_cross_modal_alignment(
            telemetry_peak_sec=t_peak_sec,
            keyframes=keyframes,
            sync_uncertainty_sec=sync_err,
            tolerance_sec=0.20,
        )

        # ----------------------------------------------------------------------
        # 4. QUALITY & STATEMENT FORMULATION
        # ----------------------------------------------------------------------
        avg_persistence = (
            sum(obs.track_persistence_frames for obs in track_obs_list) / len(track_obs_list)
            if track_obs_list
            else 0.0
        )
        occlusion_count = sum(
            1 for kf in keyframes if kf.features and kf.features.occlusion_detected
        )
        occlusion_freq = round(occlusion_count / len(keyframes), 2) if keyframes else 0.0

        quality = VisualEvidenceQuality(
            quality_rating=(
                VisualEvidenceQualityRating.HIGH
                if (active_source.frame_rate or 0) >= 25 and sync_err <= 0.05
                else VisualEvidenceQualityRating.MEDIUM
            ),
            frame_rate_fps=active_source.frame_rate,
            resolution=active_source.resolution,
            occlusion_frequency=occlusion_freq,
            sync_uncertainty_sec=sync_err,
            average_track_persistence=round(avg_persistence, 1),
            notes=[
                f"Camera: {active_source.camera_label} ({active_source.source_type})",
                f"Frame rate: {active_source.frame_rate or 'Unobserved'} fps",
                f"Sync uncertainty: +/-{sync_err}s",
            ],
        )

        is_fixture = (
            active_source.provenance is not None
            and active_source.provenance.acquisition_method == "TEST_FIXTURE"
        )
        fixture_tag = " [TEST_FIXTURE]" if is_fixture else ""

        statement = (
            f"Bounded visual evidence extracted from camera '{active_source.camera_label}'{fixture_tag}. "
            f"{len(keyframes)} keyframes analyzed across incident window. "
            f"Cross-modal alignment: {cross_modal.alignment_status.value} "
            f"(delta: {cross_modal.delta_seconds:+.3f}s, tolerance: +/-{cross_modal.tolerance_sec}s)."
        )

        limitations = [
            "Visual observations represent 2D perspective projection onto the camera plane.",
            "2D image-plane overlap (IoU) and proximity do NOT establish 3D physical contact or fault.",
            "Human steward review is required for all sporting and regulatory assessments.",
            f"Synchronization uncertainty: +/-{sync_err}s via {active_source.sync_status.value}.",
        ]

        return VisualEvidenceSummary(
            status=VisualObservationStatus.OBSERVED,
            camera_id=active_source.video_id,
            camera_label=active_source.camera_label,
            keyframes=keyframes,
            track_observations=track_obs_list,
            cross_modal_alignment=cross_modal,
            quality=quality,
            statement=statement,
            limitations=limitations,
        )


_visual_service_instance: Optional[VisualEvidenceService] = None


def get_visual_evidence_service() -> VisualEvidenceService:
    """Singleton accessor for VisualEvidenceService."""
    global _visual_service_instance
    if _visual_service_instance is None:
        _visual_service_instance = VisualEvidenceService()
    return _visual_service_instance
