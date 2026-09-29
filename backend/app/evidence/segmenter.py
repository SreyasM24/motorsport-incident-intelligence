"""Temporal segmentation and event merging for candidate episodes.

Transforms raw frame triggers into continuous, bounded interaction episodes
with well-defined event_start, event_peak, and event_end boundaries.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional
import numpy as np

from app.evidence.detector import TriggeredFrame
from app.evidence.features import FrameFeatures


@dataclass
class SegmenterConfig:
    """Configurable temporal boundaries and merging rules."""
    pre_trigger_padding_sec: float = 3.0
    post_trigger_padding_sec: float = 3.0
    merge_gap_seconds: float = 4.0
    max_episode_seconds: float = 20.0
    min_trigger_frames: int = 2


@dataclass
class SegmentedEpisode:
    """A bounded continuous temporal episode containing one or more merged triggers."""
    start_index: int
    end_index: int
    start_time_offset: float
    peak_time_offset: float
    end_time_offset: float
    start_timestamp: str
    peak_timestamp: str
    end_timestamp: str
    duration_seconds: float
    triggered_frames: List[TriggeredFrame]
    encompassing_features: List[FrameFeatures]


class EpisodeSegmenter:
    """Groups instantaneous frame triggers into cohesive temporal episodes."""

    def __init__(self, config: Optional[SegmenterConfig] = None):
        self.config = config or SegmenterConfig()

    def segment_triggers(
        self,
        triggered_frames: List[TriggeredFrame],
        all_features: List[FrameFeatures],
        dt_sec: float = 0.04,
    ) -> List[SegmentedEpisode]:
        """Cluster triggered frames, merge proximate triggers, and construct bounded episodes."""
        if not triggered_frames:
            return []

        # 1. Cluster contiguous or near-contiguous triggered frames (within merge_gap_seconds)
        clusters: List[List[TriggeredFrame]] = []
        current_cluster: List[TriggeredFrame] = [triggered_frames[0]]

        for tf in triggered_frames[1:]:
            prev_tf = current_cluster[-1]
            time_gap = tf.time_offset - prev_tf.time_offset

            if time_gap <= self.config.merge_gap_seconds:
                current_cluster.append(tf)
            else:
                clusters.append(current_cluster)
                current_cluster = [tf]

        if current_cluster:
            clusters.append(current_cluster)

        # 2. Filter out isolated transient noise (fewer than min_trigger_frames)
        valid_clusters = [
            c for c in clusters if len(c) >= self.config.min_trigger_frames
        ]

        episodes: List[SegmentedEpisode] = []
        n_total = len(all_features)

        for cluster in valid_clusters:
            # Determine peak interaction frame (minimum gap or maximum closing speed)
            min_gap_frame = min(cluster, key=lambda tf: tf.features.gap_meters)
            peak_offset = min_gap_frame.time_offset
            peak_ts = min_gap_frame.timestamp

            first_trigger_offset = cluster[0].time_offset
            last_trigger_offset = cluster[-1].time_offset

            # Bounded padding
            raw_start_offset = max(0.0, first_trigger_offset - self.config.pre_trigger_padding_sec)
            raw_end_offset = last_trigger_offset + self.config.post_trigger_padding_sec

            # Enforce max episode duration
            if (raw_end_offset - raw_start_offset) > self.config.max_episode_seconds:
                raw_end_offset = raw_start_offset + self.config.max_episode_seconds

            # Map offsets back to feature indices
            start_idx = max(0, int(round(raw_start_offset / dt_sec)))
            end_idx = min(n_total - 1, int(round(raw_end_offset / dt_sec)))

            start_feat = all_features[start_idx]
            end_feat = all_features[end_idx]

            encompassing = all_features[start_idx : end_idx + 1]
            duration = round(end_feat.time_offset - start_feat.time_offset, 2)

            episodes.append(
                SegmentedEpisode(
                    start_index=start_idx,
                    end_index=end_idx,
                    start_time_offset=start_feat.time_offset,
                    peak_time_offset=peak_offset,
                    end_time_offset=end_feat.time_offset,
                    start_timestamp=start_feat.timestamp,
                    peak_timestamp=peak_ts,
                    end_timestamp=end_feat.timestamp,
                    duration_seconds=duration,
                    triggered_frames=cluster,
                    encompassing_features=encompassing,
                )
            )

        return episodes
