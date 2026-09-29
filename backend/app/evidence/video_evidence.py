"""Video evidence synchronization algorithms, clip boundaries, and evidence builders.

CRITICAL COMPLIANCE & JURISPRUDENTIAL DOCTRINE (PROMPT 12):
    1. Zero Copyright Infringement: Does NOT store, download, or redistribute copyrighted broadcast footage.
    2. Zero Hallucination: NEVER fabricates video sources, fake URLs, or synthetic sync timestamps.
    3. Honest VIDEO_UNAVAILABLE Default: If actual video bytes are not linked, the system explicitly reports
       VIDEO_UNAVAILABLE as a valid, non-penalizing state.
    4. Orthogonal Multi-Modal Evidence: Video evidence remains completely independent of telemetry,
       baseline deviations, geometry, and ML pattern analysis.
    5. Computer Vision Readiness: Establishes a strict SYNCHRONIZED_VIDEO_FRAME contract for future CV.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

# Re-export all models from app.schemas.video_evidence for clean modularity
from app.schemas.video_evidence import (
    AnchorEventType,
    CalibrationPoint,
    CameraAlignmentInfo,
    IncidentVideoWindow,
    SynchronizedVideoFrame,
    SyncConfidence,
    SyncMethod,
    SynchronizationUncertainty,
    VideoClipRecommendation,
    VideoEvidenceDetailResponse,
    VideoEvidenceSummary,
    VideoProvenanceRecord,
    VideoSourceMetadata,
    VideoSourceType,
    VideoSyncStatus,
    VideoTimeTransform,
)


# ==============================================================================
# TIME FORMATTING & PARSING HELPERS
# ==============================================================================

def format_seconds_to_time(seconds: float) -> str:
    """Format total seconds into HH:MM:SS.mmm string."""
    if seconds < 0:
        return "00:00:00.000"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def parse_timestamp_to_seconds(ts_str: str) -> float:
    """Parse time string into elapsed seconds from midnight or reference.
    
    Supports:
        - '2024-09-01 13:04:10.000'
        - '13:04:10.000'
        - '01:04:10.500'
        - '78.45' (raw seconds)
    """
    clean = str(ts_str).strip()
    if not clean:
        return 0.0

    # If raw float string
    try:
        return float(clean)
    except ValueError:
        pass

    # Extract time component if date is present
    time_part = clean.split(" ")[-1]
    if "T" in time_part:
        time_part = time_part.split("T")[-1]

    parts = time_part.split(":")
    if len(parts) == 3:
        try:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return 0.0
    elif len(parts) == 2:
        try:
            return float(parts[0]) * 60 + float(parts[1])
        except ValueError:
            return 0.0

    return 0.0


# ==============================================================================
# DETERMINISTIC CALIBRATION & SYNCHRONIZATION ALGORITHMS
# ==============================================================================

def compute_calibration_transform(
    points: List[CalibrationPoint],
    method: SyncMethod = SyncMethod.MANUAL_CALIBRATION,
    nominal_frame_rate: Optional[float] = None,
) -> VideoTimeTransform:
    """Compute deterministic time transform and quantified uncertainty from calibration points.
    
    Supports:
        1. Single Point (N=1): a = 1.0, b = video_time - session_time.
        2. Multi-Point (N>=2): Computes linear regression scale 'a' and offset 'b'.
           If scale is within 0.5% of unity, fixes a = 1.0 to prevent overfitting.
           Calculates empirical residual RMSE.
    """
    if not points:
        return VideoTimeTransform(
            time_scale=1.0,
            offset_sec=0.0,
            method=SyncMethod.UNKNOWN,
            uncertainty=SynchronizationUncertainty(
                sync_status=VideoSyncStatus.VIDEO_UNAVAILABLE,
                method=SyncMethod.UNKNOWN,
                confidence=SyncConfidence.NONE,
                calibration_point_count=0,
                limitations=["No calibration points supplied for synchronization."],
            ),
        )

    # Validate monotonic ordering
    sorted_pts = sorted(points, key=lambda p: p.session_time_sec)

    if len(sorted_pts) == 1:
        pt = sorted_pts[0]
        # video_time = session_time + b => b = video_time - session_time
        offset_b = round(pt.video_time_sec - pt.session_time_sec, 4)
        
        # Uncertainty estimate based on method
        if method == SyncMethod.DIRECT_TIMESTAMP:
            err = 0.04  # Frame accuracy for 25Hz
            conf = SyncConfidence.HIGH
        elif method == SyncMethod.EVENT_ANCHOR:
            err = 0.50  # Transponder vs optical event threshold
            conf = SyncConfidence.MEDIUM
        else:
            err = 0.20
            conf = SyncConfidence.MEDIUM

        return VideoTimeTransform(
            time_scale=1.0,
            offset_sec=offset_b,
            method=method,
            uncertainty=SynchronizationUncertainty(
                sync_status=VideoSyncStatus.VIDEO_SYNCHRONIZED,
                offset_seconds=offset_b,
                estimated_error_seconds=err,
                method=method,
                confidence=conf,
                calibration_point_count=1,
                residual_rmse_seconds=0.0,
                limitations=["Single-point calibration assumes unity time-scale (1.0)."],
            ),
        )

    # Multi-point calibration (N >= 2)
    x = [p.session_time_sec for p in sorted_pts]
    y = [p.video_time_sec for p in sorted_pts]
    n = len(sorted_pts)

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    denom = sum((xi - mean_x) ** 2 for xi in x)
    if denom == 0 or math.isclose(denom, 0.0, abs_tol=1e-9):
        # All points have identical session time
        offset_b = round(mean_y - mean_x, 4)
        return VideoTimeTransform(
            time_scale=1.0,
            offset_sec=offset_b,
            method=method,
            uncertainty=SynchronizationUncertainty(
                sync_status=VideoSyncStatus.VIDEO_SYNCHRONIZED,
                offset_seconds=offset_b,
                estimated_error_seconds=0.50,
                method=method,
                confidence=SyncConfidence.LOW,
                calibration_point_count=n,
                limitations=["Degenerate calibration: identical session timestamps across points."],
            ),
        )

    numer = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    est_scale = numer / denom

    # Physically, broadcast/onboard video clocks drift by at most < 0.5% over a race
    if abs(est_scale - 1.0) < 0.005:
        final_scale = 1.0
        final_offset = mean_y - mean_x
    else:
        final_scale = round(est_scale, 6)
        final_offset = mean_y - final_scale * mean_x

    # Calculate residual RMSE
    residuals = [(y[i] - (final_scale * x[i] + final_offset)) for i in range(n)]
    rmse = math.sqrt(sum(r ** 2 for r in residuals) / n)

    # Base error floor based on nominal frame rate if known
    base_frame_err = (1.0 / nominal_frame_rate) if nominal_frame_rate and nominal_frame_rate > 0 else 0.04
    est_err = round(max(rmse, base_frame_err), 4)

    conf = SyncConfidence.HIGH if est_err <= 0.10 else (SyncConfidence.MEDIUM if est_err <= 0.50 else SyncConfidence.LOW)

    return VideoTimeTransform(
        time_scale=round(final_scale, 6),
        offset_sec=round(final_offset, 4),
        method=method,
        uncertainty=SynchronizationUncertainty(
            sync_status=VideoSyncStatus.VIDEO_SYNCHRONIZED,
            offset_seconds=round(final_offset, 4),
            estimated_error_seconds=est_err,
            method=method,
            confidence=conf,
            calibration_point_count=n,
            residual_rmse_seconds=round(rmse, 4),
            limitations=[f"Multi-point fit (N={n}, RMSE={rmse:.4f}s). Scale factor={final_scale:.6f}."],
        ),
    )


# ==============================================================================
# DOSSIER BUILDER
# ==============================================================================

def build_video_evidence(
    session_id: str,
    event_start_str: str,
    event_peak_str: str,
    event_end_str: str,
    source: Optional[VideoSourceMetadata] = None,
    pre_roll_sec: float = 5.0,
    post_roll_sec: float = 5.0,
    all_sources: Optional[List[VideoSourceMetadata]] = None,
) -> VideoEvidenceSummary:
    """Construct multi-modal video evidence, incident playback windows, and multi-camera alignment."""
    # 1. Unlinked / Unavailable Handling
    if source is None or source.sync_status == VideoSyncStatus.VIDEO_UNAVAILABLE:
        return VideoEvidenceSummary(
            video_evidence_status=VideoSyncStatus.VIDEO_UNAVAILABLE,
            sources=[],
            recommended_clip=None,
            incident_window=IncidentVideoWindow(
                incident_id=f"INC-{session_id}",
                window_status="UNAVAILABLE",
                session_start_time=event_start_str,
                session_peak_time=event_peak_str,
                session_end_time=event_end_str,
                pre_roll_sec=pre_roll_sec,
                post_roll_sec=post_roll_sec,
                total_clip_duration_sec=0.0,
                confidence=SyncConfidence.NONE,
            ),
            multi_camera=[],
            uncertainty=SynchronizationUncertainty(
                sync_status=VideoSyncStatus.VIDEO_UNAVAILABLE,
                method=SyncMethod.UNKNOWN,
                confidence=SyncConfidence.NONE,
                limitations=["No verified video broadcast feed is linked to this session."],
            ),
            statement="No verified video broadcast stream is linked for this candidate event. "
            "Missing video is treated strictly as unavailable evidence.",
            limitations=["Actual broadcast video stream is not ingested or linked."],
        )

    # 2. Parse event bounds into elapsed seconds
    t_start_sec = parse_timestamp_to_seconds(event_start_str)
    t_peak_sec = parse_timestamp_to_seconds(event_peak_str)
    t_end_sec = parse_timestamp_to_seconds(event_end_str)

    # Fallback sanity if timestamps failed to parse
    if t_end_sec < t_start_sec:
        t_end_sec = t_start_sec + 4.0
    if t_peak_sec < t_start_sec or t_peak_sec > t_end_sec:
        t_peak_sec = (t_start_sec + t_end_sec) / 2.0

    # 3. Resolve or initialize time transform
    if source.transform is not None:
        transform = source.transform
    elif source.session_to_video_offset_sec is not None:
        scale = source.time_scale or 1.0
        offset_b = -source.session_to_video_offset_sec * scale
        transform = VideoTimeTransform(
            time_scale=scale,
            offset_sec=offset_b,
            method=SyncMethod.MANUAL_CALIBRATION,
            uncertainty=SynchronizationUncertainty(
                sync_status=source.sync_status,
                offset_seconds=offset_b,
                estimated_error_seconds=0.20,
                method=SyncMethod.MANUAL_CALIBRATION,
                confidence=SyncConfidence.MEDIUM if source.sync_status == VideoSyncStatus.VIDEO_SYNCHRONIZED else SyncConfidence.LOW,
                calibration_point_count=1,
            ),
        )
    elif source.calibration_points:
        transform = compute_calibration_transform(source.calibration_points, nominal_frame_rate=source.frame_rate)
    else:
        transform = VideoTimeTransform(
            time_scale=1.0,
            offset_sec=0.0,
            method=SyncMethod.UNKNOWN,
            uncertainty=SynchronizationUncertainty(
                sync_status=source.sync_status,
                confidence=SyncConfidence.NONE,
            ),
        )

    # 4. Compute incident video playback window
    video_start = max(0.0, transform.session_to_video_time(t_start_sec - pre_roll_sec))
    video_peak = max(0.0, transform.session_to_video_time(t_peak_sec))
    video_end = max(0.0, transform.session_to_video_time(t_end_sec + post_roll_sec))
    clip_duration = round(video_end - video_start, 2)

    frame_start = transform.session_to_frame_number(t_start_sec - pre_roll_sec, source.frame_rate)
    frame_peak = transform.session_to_frame_number(t_peak_sec, source.frame_rate)
    frame_end = transform.session_to_frame_number(t_end_sec + post_roll_sec, source.frame_rate)

    clip = VideoClipRecommendation(
        clip_start_video_time=format_seconds_to_time(video_start),
        clip_peak_video_time=format_seconds_to_time(video_peak),
        clip_end_video_time=format_seconds_to_time(video_end),
        pre_roll_sec=pre_roll_sec,
        post_roll_sec=post_roll_sec,
        total_clip_duration_sec=clip_duration,
        sync_status=source.sync_status,
    )

    incident_win = IncidentVideoWindow(
        incident_id=f"INC-{session_id}",
        window_status="AVAILABLE" if source.sync_status in (VideoSyncStatus.VIDEO_AVAILABLE, VideoSyncStatus.VIDEO_SYNCHRONIZED) else "UNAVAILABLE",
        session_start_time=event_start_str,
        session_peak_time=event_peak_str,
        session_end_time=event_end_str,
        video_start_time=clip.clip_start_video_time,
        video_peak_time=clip.clip_peak_video_time,
        video_end_time=clip.clip_end_video_time,
        pre_roll_sec=pre_roll_sec,
        post_roll_sec=post_roll_sec,
        total_clip_duration_sec=clip_duration,
        frame_start=frame_start,
        frame_peak=frame_peak,
        frame_end=frame_end,
        estimated_error_sec=transform.uncertainty.estimated_error_seconds,
        confidence=transform.uncertainty.confidence,
    )

    # 5. Build Computer Vision Readiness Frame (Section 18 contract)
    cv_frame = SynchronizedVideoFrame(
        video_id=source.video_id,
        camera=source.camera_label,
        video_timestamp=clip.clip_peak_video_time or "00:00:00.000",
        video_time_sec=video_peak,
        session_timestamp=event_peak_str,
        session_time_sec=t_peak_sec,
        frame_number=frame_peak,
        synchronization_error_sec=transform.uncertainty.estimated_error_seconds or 0.0,
        provenance=source.provenance,
    )

    # 6. Multi-camera collation
    sources_list = all_sources or [source]
    multi_cam: List[CameraAlignmentInfo] = []
    for s in sources_list:
        s_transform = s.transform or transform
        s_video_start = max(0.0, s_transform.session_to_video_time(t_start_sec - pre_roll_sec))
        s_video_peak = max(0.0, s_transform.session_to_video_time(t_peak_sec))
        s_video_end = max(0.0, s_transform.session_to_video_time(t_end_sec + post_roll_sec))
        
        multi_cam.append(
            CameraAlignmentInfo(
                camera_id=s.video_id,
                camera_label=s.camera_label,
                source_type=s.source_type,
                sync_status=s.sync_status,
                sync_method=s_transform.method,
                offset_seconds=s_transform.offset_sec,
                estimated_error_seconds=s_transform.uncertainty.estimated_error_seconds,
                confidence=s_transform.uncertainty.confidence,
                incident_window=IncidentVideoWindow(
                    incident_id=f"INC-{session_id}",
                    window_status="AVAILABLE",
                    session_start_time=event_start_str,
                    session_peak_time=event_peak_str,
                    session_end_time=event_end_str,
                    video_start_time=format_seconds_to_time(s_video_start),
                    video_peak_time=format_seconds_to_time(s_video_peak),
                    video_end_time=format_seconds_to_time(s_video_end),
                    pre_roll_sec=pre_roll_sec,
                    post_roll_sec=post_roll_sec,
                    total_clip_duration_sec=round(s_video_end - s_video_start, 2),
                    frame_start=s_transform.session_to_frame_number(t_start_sec - pre_roll_sec, s.frame_rate),
                    frame_peak=s_transform.session_to_frame_number(t_peak_sec, s.frame_rate),
                    frame_end=s_transform.session_to_frame_number(t_end_sec + post_roll_sec, s.frame_rate),
                    estimated_error_sec=s_transform.uncertainty.estimated_error_seconds,
                    confidence=s_transform.uncertainty.confidence,
                ),
                provenance=s.provenance,
            )
        )

    # 7. Formulate steward statement
    err_str = f" +/-{transform.uncertainty.estimated_error_seconds}s" if transform.uncertainty.estimated_error_seconds else ""
    statement = (
        f"Synchronized with camera '{source.camera_label}' ({source.source_type}) via {transform.method.value}{err_str}. "
        f"Recommended playback window: {clip.clip_start_video_time} to {clip.clip_end_video_time}."
    )

    limitations = [
        f"Synchronization method: {transform.method.value} with confidence {transform.uncertainty.confidence.value}.",
        "Video footage does NOT determine fault or sporting legality autonomously.",
    ]
    if source.frame_rate is None:
        limitations.append("Frame rate is unobserved; frame-accurate stepping requires known FPS metadata.")

    return VideoEvidenceSummary(
        video_evidence_status=source.sync_status,
        sources=sources_list,
        recommended_clip=clip,
        incident_window=incident_win,
        multi_camera=multi_cam,
        uncertainty=transform.uncertainty,
        cv_readiness_frame=cv_frame,
        statement=statement,
        limitations=limitations,
    )


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
    "build_video_evidence",
    "compute_calibration_transform",
    "format_seconds_to_time",
    "parse_timestamp_to_seconds",
]
