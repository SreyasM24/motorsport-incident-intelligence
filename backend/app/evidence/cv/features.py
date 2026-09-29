"""Track-level pairwise visual interaction feature computation.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS (PROMPT 14 SECTION 8):
    1. Zero Collision / Guilt Determination: Image-plane proximity and bounding-box overlap (IoU)
       do NOT establish physical contact, breach of regulations, or driver fault.
    2. Perspective Projection Boundary: Preserves measurement_basis = BOUNDED_2D_PROJECTION.
    3. Mathematical Defensibility: Approach rate, centroid separation, and displacement are calculated
       deterministically from aligned frame observations.
"""

import math
from typing import List, Optional

from app.evidence.cv.contracts import (
    Track,
    TrackInteractionFeature,
)
from app.evidence.visual.models import ApproachTrend


def compute_track_interaction_features(
    track_a: Track,
    track_b: Track,
    event_peak_sec: float = 0.0,
    peak_video_time_sec: Optional[float] = None,
) -> List[TrackInteractionFeature]:
    """Compute frame-by-frame quantitative interaction metrics between two vehicle tracks.
    
    Args:
        track_a: First tracked vehicle sequence.
        track_b: Second tracked vehicle sequence.
        event_peak_sec: Incident peak / apex session timestamp for relative time calculation.
        peak_video_time_sec: Alias for event_peak_sec.
        
    Returns:
        List of TrackInteractionFeature records for frames where both tracks were observed.
    """
    if peak_video_time_sec is not None:
        event_peak_sec = peak_video_time_sec
    # Index observations by frame number
    obs_a_by_frame = {obs.frame_number: obs for obs in track_a.observations}
    obs_b_by_frame = {obs.frame_number: obs for obs in track_b.observations}

    common_frames = sorted(set(obs_a_by_frame.keys()).intersection(set(obs_b_by_frame.keys())))
    if not common_frames:
        return []

    features: List[TrackInteractionFeature] = []
    previous_separation: Optional[float] = None
    previous_time: Optional[float] = None

    driver_a_code = track_a.identity_association.driver_code if track_a.identity_association else None
    driver_b_code = track_b.identity_association.driver_code if track_b.identity_association else None

    for f_num in common_frames:
        obs_a = obs_a_by_frame[f_num]
        obs_b = obs_b_by_frame[f_num]

        t_video = obs_a.video_time_sec
        t_sess = obs_a.session_time_sec
        rel_time = round((t_sess if t_sess is not None else t_video) - event_peak_sec, 2)

        # 1. 2D Euclidean Centroid Separation
        sep = obs_a.bbox.centroid_distance(obs_b.bbox)

        # 2. 2D Bounding Box Overlap (IoU)
        iou = obs_a.bbox.compute_iou(obs_b.bbox)

        # 3. Relative Approach Rate (d(sep) / dt)
        approach_rate: Optional[float] = None
        trend = ApproachTrend.UNKNOWN

        if previous_separation is not None and previous_time is not None:
            dt = t_video - previous_time
            if dt > 0.001:
                d_sep = sep - previous_separation
                approach_rate = round(d_sep / dt, 4)
                if approach_rate < -0.01:
                    trend = ApproachTrend.APPROACHING
                elif approach_rate > 0.01:
                    trend = ApproachTrend.RECEDING
                else:
                    trend = ApproachTrend.STABLE

        previous_separation = sep
        previous_time = t_video

        # 4. Pixel displacement calculation
        disp_px: Optional[float] = None
        if obs_a.bbox.pixel_coords and obs_b.bbox.pixel_coords:
            p_a = obs_a.bbox.pixel_coords
            p_b = obs_b.bbox.pixel_coords
            ca_x, ca_y = p_a["x"] + p_a["w"] / 2.0, p_a["y"] + p_a["h"] / 2.0
            cb_x, cb_y = p_b["x"] + p_b["w"] / 2.0, p_b["y"] + p_b["h"] / 2.0
            disp_px = round(math.sqrt((ca_x - cb_x) ** 2 + (ca_y - cb_y) ** 2), 1)

        # 5. Occlusion & Confidence
        occluded = iou > 0.08
        mean_conf = round((obs_a.confidence + obs_b.confidence) / 2.0, 2)
        simultaneous = (not obs_a.is_interpolated) and (not obs_b.is_interpolated)

        feature = TrackInteractionFeature(
            frame_number=f_num,
            video_time_sec=t_video,
            session_time_sec=t_sess,
            event_relative_time_sec=rel_time,
            track_id_a=track_a.track_id,
            track_id_b=track_b.track_id,
            driver_a_code=driver_a_code,
            driver_b_code=driver_b_code,
            centroid_separation_norm=sep,
            bbox_overlap_iou=iou,
            relative_approach_rate_norm_per_sec=approach_rate,
            relative_displacement_px=disp_px,
            approach_recede_trend=trend,
            simultaneous_visibility=simultaneous,
            occlusion_detected=occluded,
            occlusion_ratio=iou if occluded else 0.0,
            mean_detection_confidence=mean_conf,
            temporal_continuity=not (obs_a.is_interpolated or obs_b.is_interpolated),
            measurement_basis="BOUNDED_2D_PROJECTION",
        )
        features.append(feature)

    return features
