"""Multi-Object Vehicle Tracker with deterministic track quality scoring.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS (PROMPT 14):
    1. Zero Driver Identity Assignment: The tracker assigns purely geometric identifiers
       (e.g. 'TRK-01', 'TRK-02'). It NEVER assigns driver identities (e.g. 'VER', 'HAM').
    2. Zero Hallucination: Tracks are formed strictly from detector observations and
       deterministic IoU/centroid associations.
    3. Explicit Quality Measurements: Computes concrete metrics (visibility ratio, gaps,
       fragmentation) rather than a single opaque 'AI confidence' score.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from app.evidence.cv.contracts import (
    BoundingBox,
    Detection,
    DetectionFrame,
    Track,
    TrackObservation,
    TrackQuality,
    TrackerResult,
    TrackingQualityRating,
)
from app.evidence.visual.models import VisibilityState


class VehicleTracker(ABC):
    """Abstract Base Class for multi-object vehicle tracking."""

    @abstractmethod
    def update(self, frame: DetectionFrame) -> List[Track]:
        """Update tracker state with new frame detections.
        
        Args:
            frame: Synchronized DetectionFrame containing vehicle detections.
            
        Returns:
            List of currently active Track instances.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal tracking state for a new video sequence."""
        pass

    @abstractmethod
    def get_tracks(self, active_only: bool = False) -> List[Track]:
        """Return tracked vehicle instances (optionally active only)."""
        pass

    @abstractmethod
    def get_result(self) -> TrackerResult:
        """Return complete tracking results and quality assessment."""
        pass


class DeterministicSortTracker(VehicleTracker):
    """Deterministic 2D IoU and centroid distance vehicle tracker.
    
    Provides predictable, reproducible multi-object tracking across video frames
    with explicit track continuity, gap handling, and quality classification.
    """

    def __init__(
        self,
        iou_threshold: float = 0.15,
        max_centroid_distance: float = 0.12,
        max_age: int = 3,
        min_hits: int = 2,
    ):
        self.iou_threshold = iou_threshold
        self.max_centroid_distance = max_centroid_distance
        self.max_age = max_age
        self.min_hits = min_hits

        self._next_id: int = 1
        self._tracks: Dict[str, Track] = {}
        self._track_ages: Dict[str, int] = {}          # Consecutive frames missed
        self._last_frame_number: int = -1
        self._frame_count: int = 0

    def reset(self) -> None:
        self._next_id = 1
        self._tracks.clear()
        self._track_ages.clear()
        self._last_frame_number = -1
        self._frame_count = 0

    def update(self, frame: DetectionFrame) -> List[Track]:
        """Perform bipartite matching between active tracks and incoming detections."""
        self._frame_count += 1
        f_num = frame.frame_number
        detections = frame.detections
        active_track_ids = [t_id for t_id, t in self._tracks.items() if t.is_active]

        # 1. Compute association cost matrix (IoU + centroid proximity)
        matches: List[Tuple[str, int]] = []
        unmatched_detections = set(range(len(detections)))
        unmatched_tracks = set(active_track_ids)

        if active_track_ids and detections:
            # Greedy matching sorted by best IoU / closest centroid
            pair_scores = []
            for t_id in active_track_ids:
                track = self._tracks[t_id]
                last_bbox = track.observations[-1].bbox
                for d_idx, det in enumerate(detections):
                    iou = last_bbox.compute_iou(det.bbox)
                    dist = last_bbox.centroid_distance(det.bbox)
                    # Valid match if IoU >= threshold or centroids are very close
                    if iou >= self.iou_threshold or dist <= self.max_centroid_distance:
                        # Score: higher is better
                        score = (iou * 2.0) + (1.0 - min(1.0, dist))
                        pair_scores.append((score, t_id, d_idx))

            pair_scores.sort(key=lambda x: x[0], reverse=True)
            for score, t_id, d_idx in pair_scores:
                if t_id in unmatched_tracks and d_idx in unmatched_detections:
                    matches.append((t_id, d_idx))
                    unmatched_tracks.remove(t_id)
                    unmatched_detections.remove(d_idx)

        # 2. Update matched tracks
        for t_id, d_idx in matches:
            det = detections[d_idx]
            track = self._tracks[t_id]
            self._track_ages[t_id] = 0

            obs = TrackObservation(
                observation_id=f"OBS-{t_id}-{f_num}",
                frame_number=f_num,
                video_time_sec=frame.video_time_sec,
                session_time_sec=frame.session_time_sec,
                bbox=det.bbox,
                centroid_x=det.bbox.centroid[0],
                centroid_y=det.bbox.centroid[1],
                confidence=det.confidence,
                visibility=VisibilityState.IN_FRAME,
                source_detection_id=det.detection_id,
                is_interpolated=False,
            )
            track.observations.append(obs)
            track.last_frame = f_num
            track.observation_count = len(track.observations)
            track.duration_sec = round(
                track.observations[-1].video_time_sec - track.observations[0].video_time_sec, 3
            )
            track.quality = self._calculate_track_quality(track)

        # 3. Handle unmatched tracks (missed detections / temporary disappearance)
        for t_id in unmatched_tracks:
            track = self._tracks[t_id]
            self._track_ages[t_id] += 1
            if self._track_ages[t_id] > self.max_age:
                # Terminate track
                track.is_active = False
            else:
                # Interpolate last known position as coasted observation
                last_obs = track.observations[-1]
                coasted_obs = TrackObservation(
                    observation_id=f"OBS-{t_id}-{f_num}-COAST",
                    frame_number=f_num,
                    video_time_sec=frame.video_time_sec,
                    session_time_sec=frame.session_time_sec,
                    bbox=last_obs.bbox,
                    centroid_x=last_obs.centroid_x,
                    centroid_y=last_obs.centroid_y,
                    confidence=round(last_obs.confidence * 0.85, 2),
                    visibility=VisibilityState.OCCLUDED,
                    source_detection_id=None,
                    is_interpolated=True,
                )
                track.observations.append(coasted_obs)
                track.last_frame = f_num
                track.observation_count = len(track.observations)
                track.quality = self._calculate_track_quality(track)

        # 4. Create new tracks for unmatched detections
        for d_idx in unmatched_detections:
            det = detections[d_idx]
            new_t_id = f"TRK-{self._next_id:02d}"
            self._next_id += 1
            self._track_ages[new_t_id] = 0

            initial_obs = TrackObservation(
                observation_id=f"OBS-{new_t_id}-{f_num}",
                frame_number=f_num,
                video_time_sec=frame.video_time_sec,
                session_time_sec=frame.session_time_sec,
                bbox=det.bbox,
                centroid_x=det.bbox.centroid[0],
                centroid_y=det.bbox.centroid[1],
                confidence=det.confidence,
                visibility=VisibilityState.IN_FRAME,
                source_detection_id=det.detection_id,
                is_interpolated=False,
            )
            new_track = Track(
                track_id=new_t_id,
                class_name=det.class_name,
                first_frame=f_num,
                last_frame=f_num,
                observations=[initial_obs],
                observation_count=1,
                duration_sec=0.0,
                is_active=True,
                quality=TrackQuality(rating=TrackingQualityRating.INSUFFICIENT_DATA),
            )
            new_track.quality = self._calculate_track_quality(new_track)
            self._tracks[new_t_id] = new_track

        self._last_frame_number = f_num
        return [t for t in self._tracks.values() if t.is_active]

    def _calculate_track_quality(self, track: Track) -> TrackQuality:
        """Compute explicit quality measurements and deterministic classification."""
        obs = track.observations
        count = len(obs)
        if count == 0:
            return TrackQuality(rating=TrackingQualityRating.INSUFFICIENT_DATA)

        first_f = track.first_frame
        last_f = track.last_frame
        total_span_frames = max(1, last_f - first_f + 1)
        raw_obs_count = sum(1 for o in obs if not o.is_interpolated)
        visibility_ratio = round(raw_obs_count / total_span_frames, 2)

        confidences = [o.confidence for o in obs if not o.is_interpolated]
        mean_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        min_conf = round(min(confidences), 2) if confidences else 0.0
        duration_sec = round(obs[-1].video_time_sec - obs[0].video_time_sec, 3)

        # Count gaps and fragmentation
        max_gap = 0
        current_gap = 0
        fragmentation = 0
        for o in obs:
            if o.is_interpolated:
                current_gap += 1
                max_gap = max(max_gap, current_gap)
            else:
                if current_gap > 0:
                    fragmentation += 1
                current_gap = 0

        # Deterministic classification thresholds (Prompt 14 Section 6)
        thresholds = {
            "high": "obs>=5, vis>=0.80, mean_conf>=0.80, max_gap<=2",
            "medium": "obs>=3, vis>=0.60, mean_conf>=0.65, max_gap<=4",
            "low": "obs>=2, mean_conf>=0.50",
            "insufficient": "obs<2",
        }

        if count >= 5 and visibility_ratio >= 0.80 and mean_conf >= 0.80 and max_gap <= 2:
            rating = TrackingQualityRating.HIGH
        elif count >= 3 and visibility_ratio >= 0.60 and mean_conf >= 0.65 and max_gap <= 4:
            rating = TrackingQualityRating.MEDIUM
        elif count >= 2 and mean_conf >= 0.50:
            rating = TrackingQualityRating.LOW
        else:
            rating = TrackingQualityRating.INSUFFICIENT_DATA

        return TrackQuality(
            rating=rating,
            observation_count=count,
            track_duration_sec=duration_sec,
            visibility_ratio=visibility_ratio,
            mean_confidence=mean_conf,
            minimum_confidence=min_conf,
            maximum_gap_frames=max_gap,
            fragmentation_count=fragmentation,
            thresholds_applied=thresholds,
        )

    def get_tracks(self, active_only: bool = False) -> List[Track]:
        if active_only:
            return [t for t in self._tracks.values() if t.is_active]
        return list(self._tracks.values())

    def get_result(self) -> TrackerResult:
        all_tracks = list(self._tracks.values())
        active = [t for t in all_tracks if t.is_active]
        terminated = [t for t in all_tracks if not t.is_active]
        return TrackerResult(
            tracks=all_tracks,
            active_tracks=active,
            terminated_tracks=terminated,
            total_tracks=len(all_tracks),
            frame_count=self._frame_count,
        )
