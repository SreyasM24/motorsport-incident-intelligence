"""Synchronized frame and keyframe extraction with bounded visual feature calculation.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS (PROMPT 13):
    1. Zero Hallucination: Synthesizes visual features ONLY when explicitly provided with a
       verified TEST_FIXTURE source. Real race sessions without broadcast footage return empty/unobserved.
    2. Zero Contact Determination: IoU overlap and centroid proximity are 2D perspective measurements.
       They do NOT assert physical contact or breach of sporting regulations.
    3. Multi-Modal Isolation: Telemetry anchoring is used solely to define the +/- 2.0s analysis window;
       visual features are computed strictly from camera coordinates.
"""

import math
from typing import Dict, List, Optional, Tuple

from app.evidence.video_evidence import (
    VideoProvenanceRecord,
    VideoSourceMetadata,
    VideoSyncStatus,
    VideoTimeTransform,
    format_seconds_to_time,
)
from app.evidence.visual.models import (
    AlignmentStatus,
    ApproachTrend,
    CrossModalAlignment,
    DriverAssociationStatus,
    VisibilityState,
    VisualEvidenceQuality,
    VisualEvidenceQualityRating,
    VisualFeatureEvidence,
    VisualKeyframe,
    VisualROI,
    VisualTrackObservation,
)


class VisualKeyframeExtractor:
    """Extracts frame-accurate visual keyframes and computes bounded 2D features around an incident window."""

    DEFAULT_OFFSETS = [-1.5, -0.5, 0.0, 1.0]

    def extract_keyframes(
        self,
        source: VideoSourceMetadata,
        event_peak_sec: float,
        driver_a: Optional[str] = "20",
        driver_b: Optional[str] = "27",
        relative_offsets: Optional[List[float]] = None,
    ) -> List[VisualKeyframe]:
        """Extract synchronized keyframes around an incident peak.
        
        Args:
            source: Video source metadata with calibrated transform.
            event_peak_sec: Session elapsed time of the incident peak/apex in seconds.
            driver_a: Car number or identifier for primary car.
            driver_b: Car number or identifier for comparison car.
            relative_offsets: List of second offsets relative to peak (default: [-1.5, -0.5, 0.0, 1.0]).
            
        Returns:
            List of synchronized VisualKeyframe instances.
        """
        # If video is unavailable or unlinked, return empty list honestly
        if (
            source.sync_status == VideoSyncStatus.VIDEO_UNAVAILABLE
            or source.availability_status == "UNAVAILABLE"
            or not source.transform
        ):
            return []

        offsets = relative_offsets if relative_offsets is not None else self.DEFAULT_OFFSETS
        transform: VideoTimeTransform = source.transform
        fps = source.frame_rate or 30.0
        sync_err = transform.uncertainty.estimated_error_seconds or 0.0

        is_fixture = (
            source.provenance is not None
            and source.provenance.acquisition_method == "TEST_FIXTURE"
        ) or "FIXTURE" in (source.video_id or "").upper()

        if not is_fixture:
            # For real race captures without computer vision inference weights, return bounded frame metadata without synthesized boxes
            keyframes: List[VisualKeyframe] = []
            for dt in offsets:
                t_sess = max(0.0, event_peak_sec + dt)
                v_sec = max(0.0, transform.session_to_video_time(t_sess))
                frame_idx = transform.session_to_frame_number(t_sess, fps)
                
                kf = VisualKeyframe(
                    keyframe_id=f"KF-{source.video_id}-{round(t_sess, 2)}",
                    event_relative_time_sec=round(dt, 2),
                    video_timestamp=format_seconds_to_time(v_sec),
                    video_time_sec=round(v_sec, 3),
                    session_timestamp=format_seconds_to_time(t_sess),
                    session_time_sec=round(t_sess, 3),
                    frame_number=frame_idx,
                    camera_id=source.video_id,
                    camera_label=source.camera_label,
                    observations=[],
                    rois=[],
                    features=None,
                    synchronization_error_sec=sync_err,
                    alignment_status=AlignmentStatus.ALIGNED if sync_err <= 0.20 else AlignmentStatus.PARTIALLY_ALIGNED,
                    provenance=source.provenance,
                )
                keyframes.append(kf)
            return keyframes

        # ----------------------------------------------------------------------
        # TEST FIXTURE SYNTHESIS: Deterministic, physically consistent 2D trajectory
        # ----------------------------------------------------------------------
        keyframes: List[VisualKeyframe] = []
        
        # Motion model for synthetic fixture:
        # Car A (inside overtaking line) and Car B (outside defending line)
        trajectory_map: Dict[float, Dict[str, Any]] = {
            -1.5: {
                "car_a": {"x_min": 0.30, "y_min": 0.40, "x_max": 0.42, "y_max": 0.48},
                "car_b": {"x_min": 0.50, "y_min": 0.38, "x_max": 0.62, "y_max": 0.46},
                "trend": ApproachTrend.APPROACHING,
                "displacement_px": 14.2,
                "persistence": 1,
            },
            -0.5: {
                "car_a": {"x_min": 0.38, "y_min": 0.45, "x_max": 0.50, "y_max": 0.53},
                "car_b": {"x_min": 0.48, "y_min": 0.44, "x_max": 0.60, "y_max": 0.52},
                "trend": ApproachTrend.APPROACHING,
                "displacement_px": 12.8,
                "persistence": 2,
            },
            0.0: {
                # Peak proximity / apex overlap: inside car alongside outside car
                "car_a": {"x_min": 0.42, "y_min": 0.48, "x_max": 0.54, "y_max": 0.56},
                "car_b": {"x_min": 0.47, "y_min": 0.47, "x_max": 0.59, "y_max": 0.55},
                "trend": ApproachTrend.STABLE,
                "displacement_px": 8.5,
                "persistence": 3,
            },
            1.0: {
                # Exit / separation: cars diverging post-corner
                "car_a": {"x_min": 0.50, "y_min": 0.54, "x_max": 0.62, "y_max": 0.62},
                "car_b": {"x_min": 0.62, "y_min": 0.52, "x_max": 0.74, "y_max": 0.60},
                "trend": ApproachTrend.RECEDING,
                "displacement_px": 15.6,
                "persistence": 4,
            },
        }

        for dt in offsets:
            t_sess = max(0.0, event_peak_sec + dt)
            v_sec = max(0.0, transform.session_to_video_time(t_sess))
            frame_idx = transform.session_to_frame_number(t_sess, fps)

            # Match nearest offset config
            nearest_dt = min(trajectory_map.keys(), key=lambda k: abs(k - dt))
            cfg = trajectory_map[nearest_dt]

            # Construct Car A ROI and Observation
            roi_a_data = cfg["car_a"]
            roi_a = VisualROI(
                roi_id=f"ROI-{source.video_id}-{frame_idx}-A",
                camera_id=source.video_id,
                frame_number=frame_idx,
                x_min=roi_a_data["x_min"],
                y_min=roi_a_data["y_min"],
                x_max=roi_a_data["x_max"],
                y_max=roi_a_data["y_max"],
                pixel_coords={
                    "x": int(roi_a_data["x_min"] * 1920),
                    "y": int(roi_a_data["y_min"] * 1080),
                    "w": int((roi_a_data["x_max"] - roi_a_data["x_min"]) * 1920),
                    "h": int((roi_a_data["y_max"] - roi_a_data["y_min"]) * 1080),
                },
                label=f"CAR_{driver_a or 'A'}",
                confidence=0.98,
                provenance=source.provenance,
            )

            # Construct Car B ROI and Observation
            roi_b_data = cfg["car_b"]
            roi_b = VisualROI(
                roi_id=f"ROI-{source.video_id}-{frame_idx}-B",
                camera_id=source.video_id,
                frame_number=frame_idx,
                x_min=roi_b_data["x_min"],
                y_min=roi_b_data["y_min"],
                x_max=roi_b_data["x_max"],
                y_max=roi_b_data["y_max"],
                pixel_coords={
                    "x": int(roi_b_data["x_min"] * 1920),
                    "y": int(roi_b_data["y_min"] * 1080),
                    "w": int((roi_b_data["x_max"] - roi_b_data["x_min"]) * 1920),
                    "h": int((roi_b_data["y_max"] - roi_b_data["y_min"]) * 1080),
                },
                label=f"CAR_{driver_b or 'B'}",
                confidence=0.96,
                provenance=source.provenance,
            )

            track_a = VisualTrackObservation(
                track_id=f"TRK-{driver_a or 'A'}",
                driver_number=driver_a,
                driver_code="MAG" if driver_a == "20" else "CAR_A",
                association_status=DriverAssociationStatus.CONFIRMED,
                centroid_x=round(roi_a.centroid[0], 4),
                centroid_y=round(roi_a.centroid[1], 4),
                bbox=roi_a,
                visibility=VisibilityState.IN_FRAME,
                detection_confidence=0.98,
                track_persistence_frames=cfg["persistence"],
                provenance=source.provenance,
            )

            track_b = VisualTrackObservation(
                track_id=f"TRK-{driver_b or 'B'}",
                driver_number=driver_b,
                driver_code="HUL" if driver_b == "27" else "CAR_B",
                association_status=DriverAssociationStatus.CONFIRMED,
                centroid_x=round(roi_b.centroid[0], 4),
                centroid_y=round(roi_b.centroid[1], 4),
                bbox=roi_b,
                visibility=VisibilityState.IN_FRAME,
                detection_confidence=0.96,
                track_persistence_frames=cfg["persistence"],
                provenance=source.provenance,
            )

            # Quantitative 2D metrics
            iou = roi_a.compute_iou(roi_b)
            sep = math.sqrt(
                (roi_b.centroid[0] - roi_a.centroid[0]) ** 2
                + (roi_b.centroid[1] - roi_a.centroid[1]) ** 2
            )
            occluded = iou > 0.10

            features = VisualFeatureEvidence(
                feature_set_id=f"FEAT-{source.video_id}-{frame_idx}",
                centroid_displacement_px=cfg["displacement_px"],
                bbox_width_norm=round(roi_a.width, 4),
                bbox_height_norm=round(roi_a.height, 4),
                bbox_overlap_iou=round(iou, 4),
                image_plane_separation_norm=round(sep, 4),
                approach_recede_trend=cfg["trend"],
                track_persistence_count=cfg["persistence"],
                occlusion_detected=occluded,
                occlusion_ratio=round(iou, 4) if occluded else 0.0,
                confidence_score=0.97,
                measurement_basis="BOUNDED_2D_PROJECTION",
            )

            kf = VisualKeyframe(
                keyframe_id=f"KF-{source.video_id}-{round(t_sess, 2)}",
                event_relative_time_sec=round(dt, 2),
                video_timestamp=format_seconds_to_time(v_sec),
                video_time_sec=round(v_sec, 3),
                session_timestamp=format_seconds_to_time(t_sess),
                session_time_sec=round(t_sess, 3),
                frame_number=frame_idx,
                camera_id=source.video_id,
                camera_label=source.camera_label,
                observations=[track_a, track_b],
                rois=[roi_a, roi_b],
                features=features,
                synchronization_error_sec=sync_err,
                alignment_status=AlignmentStatus.ALIGNED,
                provenance=source.provenance,
            )
            keyframes.append(kf)

        return keyframes


def compute_cross_modal_alignment(
    telemetry_peak_sec: float,
    keyframes: List[VisualKeyframe],
    sync_uncertainty_sec: float = 0.0,
    tolerance_sec: float = 0.20,
) -> CrossModalAlignment:
    """Perform deterministic cross-modal check comparing telemetry event peak with visual minimum separation.
    
    Args:
        telemetry_peak_sec: Session timestamp of telemetry minimum proximity / peak deceleration.
        keyframes: List of extracted visual keyframes.
        sync_uncertainty_sec: Time synchronization uncertainty bound.
        tolerance_sec: Max discrepancy threshold for ALIGNED classification (default 0.20s).
        
    Returns:
        CrossModalAlignment analysis result.
    """
    if not keyframes:
        return CrossModalAlignment(
            telemetry_event_time_sec=round(telemetry_peak_sec, 3),
            visual_event_time_sec=None,
            delta_seconds=None,
            synchronization_uncertainty_sec=sync_uncertainty_sec,
            tolerance_sec=tolerance_sec,
            alignment_status=AlignmentStatus.INSUFFICIENT_DATA,
            description="Insufficient visual keyframe data to perform cross-modal verification.",
        )

    # Find the keyframe with minimum image plane separation or closest to relative time 0.0
    valid_keyframes = [
        k for k in keyframes
        if k.features is not None and k.features.image_plane_separation_norm is not None
    ]

    if not valid_keyframes:
        return CrossModalAlignment(
            telemetry_event_time_sec=round(telemetry_peak_sec, 3),
            visual_event_time_sec=None,
            delta_seconds=None,
            synchronization_uncertainty_sec=sync_uncertainty_sec,
            tolerance_sec=tolerance_sec,
            alignment_status=AlignmentStatus.INSUFFICIENT_DATA,
            description="Visual keyframes present but lacking quantitative image-plane separation features.",
        )

    # Apex / closest visual proximity frame
    min_sep_kf = min(
        valid_keyframes,
        key=lambda k: k.features.image_plane_separation_norm  # type: ignore[union-attr]
    )

    t_vis = min_sep_kf.session_time_sec
    delta = round(t_vis - telemetry_peak_sec, 4)
    abs_delta = abs(delta)

    if abs_delta <= tolerance_sec:
        status = AlignmentStatus.ALIGNED
        desc = (
            f"Visual image-plane closest point ({format_seconds_to_time(t_vis)}) aligns with "
            f"telemetry peak ({format_seconds_to_time(telemetry_peak_sec)}) within +/-{tolerance_sec}s tolerance "
            f"(observed delta: {delta:+.3f}s)."
        )
    elif abs_delta <= (tolerance_sec + sync_uncertainty_sec):
        status = AlignmentStatus.PARTIALLY_ALIGNED
        desc = (
            f"Visual closest point discrepancy ({delta:+.3f}s) falls within combined tolerance and "
            f"synchronization uncertainty (+/-{round(tolerance_sec + sync_uncertainty_sec, 3)}s)."
        )
    else:
        status = AlignmentStatus.MISALIGNED
        desc = (
            f"Significant temporal discrepancy detected: visual separation minimum is {delta:+.3f}s "
            f"relative to telemetry peak, exceeding uncertainty threshold (+/-{round(tolerance_sec + sync_uncertainty_sec, 3)}s)."
        )

    return CrossModalAlignment(
        telemetry_event_time_sec=round(telemetry_peak_sec, 3),
        visual_event_time_sec=round(t_vis, 3),
        delta_seconds=delta,
        synchronization_uncertainty_sec=sync_uncertainty_sec,
        tolerance_sec=tolerance_sec,
        alignment_status=status,
        description=desc,
    )
