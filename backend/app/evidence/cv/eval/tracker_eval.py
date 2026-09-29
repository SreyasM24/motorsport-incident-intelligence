"""Multi-Object Tracking (MOT) evaluation engine.

Measures track continuity, ID switches (IDSW), track fragmentation, and
strictly distinguishes detection errors from tracking errors.
"""

from collections import defaultdict
import statistics
from typing import Dict, List, Optional, Set, Tuple

from app.evidence.cv.contracts import Track
from app.evidence.cv.eval.contracts import FailureCategory, GroundTruthAnnotation, TrackingEvaluationMetrics


class TrackingEvaluator:
    """Evaluates multi-object tracker outputs against ground-truth track sequences."""

    def __init__(self, iou_threshold: float = 0.50):
        self.iou_threshold = iou_threshold

    def evaluate_tracks(
        self,
        ground_truth_by_frame: Dict[int, List[GroundTruthAnnotation]],
        predicted_tracks: List[Track],
    ) -> Tuple[TrackingEvaluationMetrics, Dict[str, int]]:
        """Evaluate predicted tracks against frame-indexed ground truth annotations.

        Returns:
            Tuple of (TrackingEvaluationMetrics, failure_counts_dict)
        """
        failures: Dict[str, int] = defaultdict(int)

        # 1. Group GT annotations by GT track ID
        gt_track_frames: Dict[str, List[Tuple[int, GroundTruthAnnotation]]] = defaultdict(list)
        for frame_idx, annotations in ground_truth_by_frame.items():
            for ann in annotations:
                track_id = ann.track_id or f"GT-{ann.object_id}"
                gt_track_frames[track_id].append((frame_idx, ann))

        total_gt_tracks = len(gt_track_frames)
        total_pred_tracks = len(predicted_tracks)

        if total_gt_tracks == 0:
            return (
                TrackingEvaluationMetrics(
                    total_gt_tracks=0,
                    total_pred_tracks=total_pred_tracks,
                    track_continuity_ratio=0.0,
                    statement="Zero ground-truth tracks present in evaluation set.",
                ),
                dict(failures),
            )

        # 2. Build index of predicted observations by (frame_number, track_id)
        pred_obs_by_frame: Dict[int, List[Tuple[str, Any]]] = defaultdict(list)
        for track in predicted_tracks:
            for obs in track.observations:
                pred_obs_by_frame[obs.frame_number].append((track.track_id, obs))

        # 3. Match each GT observation to predicted tracks frame by frame
        # Mapping: gt_track_id -> list of matched pred_track_ids (or None if missed)
        gt_match_history: Dict[str, List[Tuple[int, Optional[str]]]] = defaultdict(list)
        total_gt_observations = 0
        missed_observations = 0
        detection_errors = 0
        tracking_errors = 0

        for gt_track_id, observations in gt_track_frames.items():
            observations.sort(key=lambda x: x[0])  # sort by frame number
            for frame_idx, gt_ann in observations:
                total_gt_observations += 1
                preds_in_frame = pred_obs_by_frame.get(frame_idx, [])

                best_match: Optional[str] = None
                best_iou = 0.0

                for pred_track_id, obs in preds_in_frame:
                    iou = obs.bbox.compute_iou(gt_ann.bounding_box)
                    if iou >= self.iou_threshold and iou > best_iou:
                        best_match = pred_track_id
                        best_iou = iou

                gt_match_history[gt_track_id].append((frame_idx, best_match))

                if best_match is None:
                    missed_observations += 1
                    # Check whether there was any detection at all in the frame
                    if len(preds_in_frame) == 0:
                        detection_errors += 1
                    else:
                        tracking_errors += 1

        # 4. Compute ID Switches (IDSW) and Fragmentations
        id_switches = 0
        track_fragmentations = 0
        continuity_scores: List[float] = []

        for gt_track_id, history in gt_match_history.items():
            last_matched_pred: Optional[str] = None
            observed_count = 0
            first_frame = history[0][0]
            last_frame = history[-1][0]
            lifespan_frames = max(1, last_frame - first_frame + 1)

            was_gap = False

            for frame_idx, matched_pred in history:
                if matched_pred is not None:
                    observed_count += 1
                    if last_matched_pred is not None and matched_pred != last_matched_pred:
                        id_switches += 1
                        failures[FailureCategory.IDENTITY_AMBIGUITY.value] += 1
                    if was_gap:
                        track_fragmentations += 1
                        failures[FailureCategory.TRACK_FRAGMENTATION.value] += 1
                        was_gap = False
                    last_matched_pred = matched_pred
                else:
                    if last_matched_pred is not None:
                        was_gap = True

            continuity = round(float(observed_count / lifespan_frames), 4)
            continuity_scores.append(continuity)

        mean_continuity = (
            round(statistics.mean(continuity_scores), 4) if continuity_scores else 0.0
        )

        # 5. Track Durations
        durations = [t.duration_sec for t in predicted_tracks if t.duration_sec > 0]
        mean_duration = round(statistics.mean(durations), 4) if durations else 0.0

        # 6. MOTA calculation approximation
        # MOTA = 1 - (missed_obs + fp_obs + id_switches) / total_gt_obs
        total_pred_obs = sum(len(t.observations) for t in predicted_tracks)
        matched_obs_count = total_gt_observations - missed_observations
        fp_observations = max(0, total_pred_obs - matched_obs_count)

        mota_numerator = missed_observations + fp_observations + id_switches
        mota = (
            round(float(1.0 - (mota_numerator / total_gt_observations)), 4)
            if total_gt_observations > 0
            else None
        )

        metrics = TrackingEvaluationMetrics(
            total_gt_tracks=total_gt_tracks,
            total_pred_tracks=total_pred_tracks,
            id_switches=id_switches,
            track_fragmentations=track_fragmentations,
            track_continuity_ratio=mean_continuity,
            mean_track_duration_sec=mean_duration,
            missed_observations=missed_observations,
            detection_errors=detection_errors,
            tracking_errors=tracking_errors,
            mota=mota,
            statement=(
                f"Evaluated {total_gt_tracks} ground truth tracks against {total_pred_tracks} predicted tracks. "
                f"ID Switches: {id_switches}, Fragmentations: {track_fragmentations}."
            ),
        )

        return metrics, dict(failures)
