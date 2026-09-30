"""Cross-modal temporal and spatial synchronization evaluation engine.

Measures temporal discrepancy between visual minimum separation and telemetry
proximity events against authoritative annotations, as well as spatial discrepancy
between 2D track projection and visual image planes.

CRITICAL GUARDRAIL (Prompt 22):
    Any cross-modal spatial or temporal discrepancy is an EVIDENCE-QUALITY FLAG,
    reflecting sensor alignment uncertainty, optical distortion, or timecode drift.
    It NEVER constitutes driver fault, sporting guilt, or collision liability.
"""

import statistics
from typing import Dict, List, Optional, Tuple
from app.evidence.cv.eval.contracts import CrossModalEvaluationMetrics
from app.evidence.visual.models import AlignmentStatus


class CrossModalEvaluator:
    """Evaluates cross-modal time synchronization and spatial correspondence."""

    @staticmethod
    def evaluate_cross_modal_events(
        event_pairs: List[Tuple[float, float, float]],  # (telemetry_sec, visual_sec, sync_uncertainty_sec)
        tolerance_sec: float = 0.20,
        spatial_discrepancies_m: Optional[List[float]] = None,
    ) -> CrossModalEvaluationMetrics:
        """Evaluate temporal and spatial discrepancies across verified incident events.

        If event_pairs is empty, reports NOT_AVAILABLE honestly.
        """
        if not event_pairs:
            return CrossModalEvaluationMetrics(
                evaluation_status="NOT_AVAILABLE",
                total_events_evaluated=0,
                spatial_alignment_status="NOT_EVALUATED",
                statement=(
                    "Cross-modal evaluation is NOT_AVAILABLE. Real race event visual ground-truth "
                    "timecodes are unlabelled or unlinked due to commercial licensing restrictions."
                ),
            )

        diffs = [abs(t_vis - t_tel) for t_tel, t_vis, _ in event_pairs]
        mean_diff = round(statistics.mean(diffs), 4)
        median_diff = round(statistics.median(diffs), 4)
        max_diff = round(max(diffs), 4)
        mean_uncertainty = round(statistics.mean([sigma for _, _, sigma in event_pairs]), 4)

        aligned = 0
        partially_aligned = 0
        misaligned = 0

        for t_tel, t_vis, sigma in event_pairs:
            diff = abs(t_vis - t_tel)
            if diff <= tolerance_sec:
                aligned += 1
            elif diff <= tolerance_sec + sigma:
                partially_aligned += 1
            else:
                misaligned += 1

        # Evaluate spatial discrepancy if provided
        mean_spatial_m: Optional[float] = None
        spatial_status = "NOT_EVALUATED"
        if spatial_discrepancies_m and len(spatial_discrepancies_m) > 0:
            mean_spatial_m = round(statistics.mean(spatial_discrepancies_m), 3)
            if mean_spatial_m <= 0.5:
                spatial_status = "TIGHT_CORRESPONDENCE"
            elif mean_spatial_m <= 1.5:
                spatial_status = "ACCEPTABLE_CORRESPONDENCE"
            else:
                spatial_status = "PROJECTION_DISCREPANCY_FLAG"

        return CrossModalEvaluationMetrics(
            evaluation_status="EVALUATED",
            total_events_evaluated=len(event_pairs),
            mean_absolute_difference_sec=mean_diff,
            median_difference_sec=median_diff,
            max_difference_sec=max_diff,
            uncertainty_interval_sec=mean_uncertainty,
            aligned_count=aligned,
            partially_aligned_count=partially_aligned,
            misaligned_count=misaligned,
            spatial_discrepancy_m=mean_spatial_m,
            spatial_alignment_status=spatial_status,
            discrepancy_interpretation="DISCREPANCY_IS_EVIDENCE_QUALITY_FLAG_NOT_DRIVER_FAULT",
            statement=(
                f"Evaluated {len(event_pairs)} event pairs: {aligned} aligned, "
                f"{partially_aligned} partially aligned, {misaligned} misaligned. "
                f"Mean temporal delta: {mean_diff:.3f}s. "
                "Any discrepancy is an evidence-quality and synchronization flag, NOT driver fault."
            ),
        )
