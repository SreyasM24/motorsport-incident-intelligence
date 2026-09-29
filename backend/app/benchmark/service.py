"""Benchmark orchestration service providing benchmark evaluation and comparative search."""

from typing import Any, Dict, List, Optional
from app.benchmark.manifest import (
    BenchmarkManifest,
    HistoricalIncidentCase,
    load_benchmark_manifest,
)
from app.benchmark.evaluator import (
    BenchmarkSuiteReport,
    CaseEvaluationReport,
    HistoricalReconstructionEvaluator,
)
from app.benchmark.comparator import (
    ComparableIncidentMatch,
    HistoricalCaseComparator,
)


class BenchmarkService:
    """Singleton service for historical incident benchmark suite execution."""

    def __init__(self, manifest: Optional[BenchmarkManifest] = None):
        self.manifest = manifest or load_benchmark_manifest()
        self.evaluator = HistoricalReconstructionEvaluator(self.manifest.tolerances)
        self.comparator = HistoricalCaseComparator(self.manifest)
        self._cached_suite_report: Optional[BenchmarkSuiteReport] = None

    def get_manifest(self) -> BenchmarkManifest:
        """Return the raw benchmark manifest."""
        return self.manifest

    def get_cases(self) -> List[HistoricalIncidentCase]:
        """Return all benchmark cases."""
        return self.manifest.cases

    def get_case_by_id(self, case_id: str) -> Optional[HistoricalIncidentCase]:
        """Retrieve a specific benchmark case by ID."""
        for c in self.manifest.cases:
            if c.case_id == case_id:
                return c
        return None

    def run_benchmark_suite(self, force_refresh: bool = False) -> BenchmarkSuiteReport:
        """Run the full historical incident reconstruction benchmark suite."""
        if self._cached_suite_report and not force_refresh:
            return self._cached_suite_report

        report = self.evaluator.evaluate_manifest(self.manifest)
        self._cached_suite_report = report
        return report

    def evaluate_single_case(self, case_id: str) -> Optional[CaseEvaluationReport]:
        """Evaluate a single benchmark case by ID."""
        case = self.get_case_by_id(case_id)
        if not case:
            return None
        return self.evaluator.evaluate_case(case)

    def find_comparable_cases(
        self,
        case_id: str,
        top_k: int = 3,
    ) -> List[ComparableIncidentMatch]:
        """Find empirically comparable historical incidents based on observable features."""
        return self.comparator.find_comparable_incidents(query_case_id=case_id, top_k=top_k)

    def get_provenance_matrix(self):
        """Return the authoritative ground-truth vs system independence audit matrix."""
        return self.evaluator.audit_metric_provenance()

    def get_group_splits(self, split_type: str = "circuit") -> Dict[str, Any]:
        """Generate leakage-free cross-validation splits by circuit, season, or event."""
        from app.benchmark.manifest import (
            leave_one_circuit_out_splits,
            leave_one_season_out_splits,
            leave_one_event_out_splits,
        )
        if split_type == "season":
            raw_splits = leave_one_season_out_splits(self.manifest, verified_only=True)
        elif split_type == "event":
            raw_splits = leave_one_event_out_splits(self.manifest, verified_only=True)
        else:
            raw_splits = leave_one_circuit_out_splits(self.manifest, verified_only=True)

        serialized: Dict[str, Any] = {}
        for key, fold in raw_splits.items():
            serialized[key] = {
                "trainCount": len(fold["train"]),
                "testCount": len(fold["test"]),
                "trainCaseIds": [c.case_id for c in fold["train"]],
                "testCaseIds": [c.case_id for c in fold["test"]],
            }
        return serialized

    def evaluate_comparator(self, top_k: int = 3):
        """Evaluate observable physical similarity and feature isolation of comparator."""
        return self.comparator.evaluate_observable_similarity(top_k=top_k)

    def audit_comparator_isolation(self) -> Dict[str, Any]:
        """Audit that comparator scoring is strictly isolated from historical penalties."""
        return self.comparator.audit_feature_isolation()


_benchmark_service_instance: Optional[BenchmarkService] = None


def get_benchmark_service() -> BenchmarkService:
    """Retrieve or initialize the global BenchmarkService instance."""
    global _benchmark_service_instance
    if _benchmark_service_instance is None:
        _benchmark_service_instance = BenchmarkService()
    return _benchmark_service_instance
