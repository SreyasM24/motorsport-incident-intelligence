"""Driver visual identity evaluation engine.

Measures accuracy of driver attribution against certified ground truth annotations.
Honestly reports INSUFFICIENT_DATA when independent real identity ground truth is absent.
"""

from typing import Dict, List, Optional
from app.evidence.cv.contracts import VisualIdentityAssociation
from app.evidence.cv.eval.contracts import (
    AnnotationIdentityStatus,
    GroundTruthAnnotation,
    IdentityEvaluationMetrics,
)


class IdentityEvaluator:
    """Evaluates visual driver identity associations against ground-truth labels."""

    @staticmethod
    def evaluate_associations(
        ground_truth: List[GroundTruthAnnotation],
        predicted_associations: List[VisualIdentityAssociation],
        is_synthetic: bool = False,
    ) -> IdentityEvaluationMetrics:
        """Evaluate identity associations.

        CRITICAL GUARDRAIL (Prompt 22):
            Driver identity attribution requires authoritative camera metadata, helmet, or
            car livery annotations. If not independently verified, MUST report
            IDENTITY_EVALUATION = INSUFFICIENT_DATA.
            Never infer or fabricate real-world identity accuracy from synthetic fixtures.
        """
        # Filter GT that have an identity label
        annotated_gt = [
            gt for gt in ground_truth
            if gt.identity_status == AnnotationIdentityStatus.CONFIRMED and gt.identity_label
        ]

        if is_synthetic:
            return IdentityEvaluationMetrics(
                evaluation_status="NOT_AVAILABLE",
                total_evaluated=len(annotated_gt),
                statement=(
                    "Real-world driver identity evaluation is NOT_AVAILABLE (INSUFFICIENT_DATA). "
                    "Official broadcast video car livery/helmet/onboard metadata annotations are not present. "
                    "Accuracy metrics will not be claimed from synthetic test fixtures."
                ),
            )

        if not annotated_gt:
            return IdentityEvaluationMetrics(
                evaluation_status="INSUFFICIENT_DATA",
                total_evaluated=0,
                statement=(
                    "Driver identity evaluation status: INSUFFICIENT_DATA. "
                    "Independent optical livery, helmet, or car number ground truth annotations "
                    "are not present in dataset. Real-world accuracy metrics cannot be asserted."
                ),
            )

        # Build mapping of GT track/object ID to driver code
        gt_driver_map: Dict[str, str] = {}
        for gt in annotated_gt:
            key = gt.track_id or gt.object_id
            gt_driver_map[key] = gt.identity_label.upper()

        correct = 0
        incorrect = 0
        unknown = 0
        not_annotated = 0

        for pred in predicted_associations:
            gt_driver = gt_driver_map.get(pred.track_id)
            if not gt_driver:
                not_annotated += 1
                continue

            if not pred.driver_code:
                unknown += 1
            elif pred.driver_code.upper() == gt_driver:
                correct += 1
            else:
                incorrect += 1

        total = correct + incorrect + unknown
        accuracy = round(float(correct / total), 4) if total > 0 else 0.0
        unknown_rate = round(float(unknown / total), 4) if total > 0 else 0.0
        incorrect_rate = round(float(incorrect / total), 4) if total > 0 else 0.0

        return IdentityEvaluationMetrics(
            evaluation_status="EVALUATED",
            total_evaluated=total,
            correct_count=correct,
            incorrect_count=incorrect,
            unknown_count=unknown,
            not_annotated_count=not_annotated,
            identity_accuracy=accuracy,
            unknown_rate=unknown_rate,
            incorrect_rate=incorrect_rate,
            statement=(
                f"Evaluated {total} associations: {correct} correct, {incorrect} incorrect, "
                f"{unknown} unknown. Accuracy: {accuracy * 100:.1f}%."
            ),
        )
