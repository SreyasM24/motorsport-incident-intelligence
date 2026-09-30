"""Leakage-safe group-based dataset partition manager.

CRITICAL GUARDRAIL:
    Never split adjacent frames from the same video or camera sequence across
    train and test sets. Partitions must be grouped strictly by Event, Session,
    or Video/Camera.
"""

from typing import Any, Dict, List, Set, Tuple
from app.evidence.cv.eval.contracts import DatasetSampleManifest


class GroupSplitter:
    """Partitions dataset samples into train, val, and test splits using grouping keys."""

    @staticmethod
    def partition_samples_by_group(
        samples: List[DatasetSampleManifest],
        group_key: str = "session",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Dict[str, List[DatasetSampleManifest]]:
        """Partition samples into train/val/test splits grouped strictly by session/video/event.

        Guarantees that all samples sharing the same group key remain exclusively within
        one partition.
        """
        if not samples:
            return {"train": [], "val": [], "test": []}

        # 1. Group samples by group_key
        grouped: Dict[str, List[DatasetSampleManifest]] = {}
        for sample in samples:
            val = getattr(sample, group_key, None) or sample.source_video
            grouped.setdefault(str(val), []).append(sample)

        group_names = sorted(list(grouped.keys()))
        total_groups = len(group_names)

        if total_groups == 1:
            # Single group cannot be safely split without temporal leakage
            # Allocate to test or train depending on use case, here default to test for evaluation
            return {"train": [], "val": [], "test": samples}

        n_train = max(1, int(round(total_groups * train_ratio)))
        n_val = max(1, int(round(total_groups * val_ratio))) if total_groups >= 3 else 0

        train_groups = set(group_names[:n_train])
        val_groups = set(group_names[n_train : n_train + n_val])
        test_groups = set(group_names[n_train + n_val :])

        if not test_groups and total_groups >= 2:
            # Ensure test group is not empty if we have at least 2 groups
            test_groups = {group_names[-1]}
            train_groups.discard(group_names[-1])
            val_groups.discard(group_names[-1])

        # Verify strict zero-leakage invariant
        assert len(train_groups & val_groups) == 0, "Train-Val group leakage detected!"
        assert len(train_groups & test_groups) == 0, "Train-Test group leakage detected!"
        assert len(val_groups & test_groups) == 0, "Val-Test group leakage detected!"

        train_samples = [s for g in train_groups for s in grouped[g]]
        val_samples = [s for g in val_groups for s in grouped[g]]
        test_samples = [s for g in test_groups for s in grouped[g]]

        return {
            "train": train_samples,
            "val": val_samples,
            "test": test_samples,
        }

    @staticmethod
    def leave_one_video_out(samples: List[DatasetSampleManifest]) -> List[Dict[str, Any]]:
        """Generate Leave-One-Video-Out (LOVO) cross-validation folds.

        Each fold holds out exactly one video as test, using remaining videos for train/val.
        Guarantees zero frame leakage across video boundaries.
        """
        if not samples:
            return []

        videos: Dict[str, List[DatasetSampleManifest]] = {}
        for s in samples:
            v_key = s.source_video or s.sample_id
            videos.setdefault(v_key, []).append(s)

        video_keys = sorted(list(videos.keys()))
        folds: List[Dict[str, Any]] = []

        for held_out_idx, held_out_video in enumerate(video_keys):
            test_samples = videos[held_out_video]
            train_samples = [
                s for v_key, s_list in videos.items() if v_key != held_out_video for s in s_list
            ]

            # Invariant check: no leakage
            assert GroupSplitter.verify_no_leakage(train_samples, test_samples, group_key="source_video")

            folds.append(
                {
                    "fold_index": held_out_idx,
                    "held_out_video": held_out_video,
                    "train_sample_count": len(train_samples),
                    "test_sample_count": len(test_samples),
                    "train_samples": train_samples,
                    "test_samples": test_samples,
                }
            )

        return folds

    @staticmethod
    def leave_one_event_out(samples: List[DatasetSampleManifest]) -> List[Dict[str, Any]]:
        """Generate Leave-One-Event-Out (LOEO) cross-validation folds.

        Each fold holds out an entire racing event (grand prix / circuit).
        Guarantees zero environmental or track-geometry leakage into test set.
        """
        if not samples:
            return []

        events: Dict[str, List[DatasetSampleManifest]] = {}
        for s in samples:
            e_key = s.event or "DEFAULT_EVENT"
            events.setdefault(e_key, []).append(s)

        event_keys = sorted(list(events.keys()))
        folds: List[Dict[str, Any]] = []

        for held_out_idx, held_out_event in enumerate(event_keys):
            test_samples = events[held_out_event]
            train_samples = [
                s for e_key, s_list in events.items() if e_key != held_out_event for s in s_list
            ]

            # Invariant check: no leakage
            assert GroupSplitter.verify_no_leakage(train_samples, test_samples, group_key="event")

            folds.append(
                {
                    "fold_index": held_out_idx,
                    "held_out_event": held_out_event,
                    "train_sample_count": len(train_samples),
                    "test_sample_count": len(test_samples),
                    "train_samples": train_samples,
                    "test_samples": test_samples,
                }
            )

        return folds

    @staticmethod
    def verify_no_leakage(
        train_samples: List[DatasetSampleManifest],
        test_samples: List[DatasetSampleManifest],
        group_key: str = "session",
    ) -> bool:
        """Verify that no group key is shared between train and test partitions."""
        train_keys: Set[str] = {
            str(getattr(s, group_key, None) or s.source_video) for s in train_samples
        }
        test_keys: Set[str] = {
            str(getattr(s, group_key, None) or s.source_video) for s in test_samples
        }
        intersection = train_keys & test_keys
        return len(intersection) == 0
