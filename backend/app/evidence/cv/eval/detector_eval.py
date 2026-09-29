"""Vehicle detection evaluation engine.

Measures detection precision, recall, F1, IoU distributions, and categorizes
detector errors (misses, duplicates, small vehicles, heavy occlusion).
"""

from collections import defaultdict
import statistics
from typing import Dict, List, Optional, Tuple

from app.evidence.cv.contracts import BoundingBox, Detection
from app.evidence.cv.eval.contracts import (
    DetectionEvaluationMetrics,
    FailureCategory,
    GroundTruthAnnotation,
)


class DetectionEvaluator:
    """Evaluates vehicle detector hypotheses against ground-truth bounding box annotations."""

    def __init__(self, iou_threshold: float = 0.50):
        self.iou_threshold = iou_threshold

    def evaluate_detections(
        self,
        ground_truth: List[GroundTruthAnnotation],
        predictions: List[Detection],
    ) -> Tuple[DetectionEvaluationMetrics, Dict[str, int]]:
        """Evaluate predicted detections against ground truth annotations.

        Returns:
            Tuple of (DetectionEvaluationMetrics, failure_counts_dict)
        """
        total_gt = len(ground_truth)
        total_pred = len(predictions)

        failures: Dict[str, int] = defaultdict(int)

        if total_gt == 0 and total_pred == 0:
            return (
                DetectionEvaluationMetrics(
                    total_ground_truth=0,
                    total_predictions=0,
                    precision=1.0,
                    recall=1.0,
                    f1_score=1.0,
                    iou_threshold=self.iou_threshold,
                ),
                dict(failures),
            )

        if total_gt == 0 and total_pred > 0:
            failures[FailureCategory.DUPLICATE_DETECTION.value] += total_pred
            return (
                DetectionEvaluationMetrics(
                    total_ground_truth=0,
                    total_predictions=total_pred,
                    false_positives=total_pred,
                    precision=0.0,
                    recall=0.0,
                    f1_score=0.0,
                    iou_threshold=self.iou_threshold,
                ),
                dict(failures),
            )

        if total_gt > 0 and total_pred == 0:
            for gt in ground_truth:
                failures[FailureCategory.DETECTOR_MISS.value] += 1
                if gt.bounding_box.area < 0.01:
                    failures[FailureCategory.SMALL_VEHICLE.value] += 1
                if gt.occlusion > 0.40:
                    failures[FailureCategory.HEAVY_OCCLUSION.value] += 1

            return (
                DetectionEvaluationMetrics(
                    total_ground_truth=total_gt,
                    total_predictions=0,
                    false_negatives=total_gt,
                    precision=0.0,
                    recall=0.0,
                    f1_score=0.0,
                    iou_threshold=self.iou_threshold,
                ),
                dict(failures),
            )

        # Match predictions to GT using greedy IoU bipartite assignment
        # Sort predictions by confidence descending
        sorted_preds = sorted(predictions, key=lambda p: p.confidence, reverse=True)

        matched_gt_indices = set()
        matched_pred_indices = set()
        tp_ious: List[float] = []
        duplicate_count = 0

        # Matrix of IoUs
        iou_pairs: List[Tuple[float, int, int]] = []
        for p_idx, pred in enumerate(sorted_preds):
            for gt_idx, gt in enumerate(ground_truth):
                iou = pred.bbox.compute_iou(gt.bounding_box)
                if iou >= self.iou_threshold:
                    iou_pairs.append((iou, p_idx, gt_idx))

        # Sort matches by IoU descending
        iou_pairs.sort(key=lambda x: x[0], reverse=True)

        gt_match_counts = defaultdict(int)

        for iou, p_idx, gt_idx in iou_pairs:
            if p_idx not in matched_pred_indices:
                if gt_idx not in matched_gt_indices:
                    matched_gt_indices.add(gt_idx)
                    matched_pred_indices.add(p_idx)
                    gt_match_counts[gt_idx] += 1
                    tp_ious.append(iou)
                else:
                    # Duplicate detection matching an already-claimed GT box
                    duplicate_count += 1
                    matched_pred_indices.add(p_idx)
                    failures[FailureCategory.DUPLICATE_DETECTION.value] += 1

        tp = len(matched_gt_indices)
        fp = (total_pred - tp)
        fn = total_gt - tp

        precision = round(float(tp / (tp + fp)), 4) if (tp + fp) > 0 else 0.0
        recall = round(float(tp / (tp + fn)), 4) if (tp + fn) > 0 else 0.0
        f1 = (
            round(float(2 * precision * recall / (precision + recall)), 4)
            if (precision + recall) > 0
            else 0.0
        )

        mean_iou = round(statistics.mean(tp_ious), 4) if tp_ious else 0.0
        median_iou = round(statistics.median(tp_ious), 4) if tp_ious else 0.0
        min_iou = round(min(tp_ious), 4) if tp_ious else 0.0
        max_iou = round(max(tp_ious), 4) if tp_ious else 0.0

        # Categorize missed GT errors
        for gt_idx, gt in enumerate(ground_truth):
            if gt_idx not in matched_gt_indices:
                failures[FailureCategory.DETECTOR_MISS.value] += 1
                if gt.bounding_box.area < 0.01:
                    failures[FailureCategory.SMALL_VEHICLE.value] += 1
                elif gt.bounding_box.area < 0.03:
                    failures[FailureCategory.DISTANT_VEHICLE.value] += 1

                if gt.occlusion > 0.40:
                    failures[FailureCategory.HEAVY_OCCLUSION.value] += 1
                elif gt.occlusion > 0.10:
                    failures[FailureCategory.PARTIAL_VISIBILITY.value] += 1

        # Breakdown by size
        size_breakdown: Dict[str, Dict[str, Any]] = {
            "small": {"gt_count": 0, "tp_count": 0, "recall": 0.0},
            "medium": {"gt_count": 0, "tp_count": 0, "recall": 0.0},
            "large": {"gt_count": 0, "tp_count": 0, "recall": 0.0},
        }

        for gt_idx, gt in enumerate(ground_truth):
            area = gt.bounding_box.area
            size_bucket = "small" if area < 0.01 else ("medium" if area < 0.05 else "large")
            size_breakdown[size_bucket]["gt_count"] += 1
            if gt_idx in matched_gt_indices:
                size_breakdown[size_bucket]["tp_count"] += 1

        for bucket in size_breakdown.values():
            if bucket["gt_count"] > 0:
                bucket["recall"] = round(float(bucket["tp_count"] / bucket["gt_count"]), 4)

        # Breakdown by occlusion
        occlusion_breakdown: Dict[str, Dict[str, Any]] = {
            "unoccluded": {"gt_count": 0, "tp_count": 0, "recall": 0.0},
            "partially_occluded": {"gt_count": 0, "tp_count": 0, "recall": 0.0},
            "heavily_occluded": {"gt_count": 0, "tp_count": 0, "recall": 0.0},
        }

        for gt_idx, gt in enumerate(ground_truth):
            occ = gt.occlusion
            occ_bucket = (
                "unoccluded"
                if occ < 0.10
                else ("partially_occluded" if occ <= 0.50 else "heavily_occluded")
            )
            occlusion_breakdown[occ_bucket]["gt_count"] += 1
            if gt_idx in matched_gt_indices:
                occlusion_breakdown[occ_bucket]["tp_count"] += 1

        for bucket in occlusion_breakdown.values():
            if bucket["gt_count"] > 0:
                bucket["recall"] = round(float(bucket["tp_count"] / bucket["gt_count"]), 4)

        # Approximate AP@50 and AP@75
        ap_50 = precision if self.iou_threshold == 0.50 else None
        ap_75 = (
            self._evaluate_at_threshold(ground_truth, sorted_preds, 0.75)
            if self.iou_threshold <= 0.75
            else None
        )

        metrics = DetectionEvaluationMetrics(
            total_ground_truth=total_gt,
            total_predictions=total_pred,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            duplicate_detections=duplicate_count,
            precision=precision,
            recall=recall,
            f1_score=f1,
            iou_threshold=self.iou_threshold,
            mean_iou=mean_iou,
            median_iou=median_iou,
            min_iou=min_iou,
            max_iou=max_iou,
            ap_50=ap_50,
            ap_75=ap_75,
            breakdown_by_size=size_breakdown,
            breakdown_by_occlusion=occlusion_breakdown,
        )

        return metrics, dict(failures)

    def _evaluate_at_threshold(
        self,
        ground_truth: List[GroundTruthAnnotation],
        sorted_preds: List[Detection],
        threshold: float,
    ) -> float:
        """Helper to compute precision at a specific IoU threshold."""
        matched_gt = set()
        matched_p = set()
        for p_idx, pred in enumerate(sorted_preds):
            for gt_idx, gt in enumerate(ground_truth):
                if gt_idx not in matched_gt and p_idx not in matched_p:
                    if pred.bbox.compute_iou(gt.bounding_box) >= threshold:
                        matched_gt.add(gt_idx)
                        matched_p.add(p_idx)
        tp = len(matched_gt)
        fp = len(sorted_preds) - tp
        return round(float(tp / (tp + fp)), 4) if (tp + fp) > 0 else 0.0
