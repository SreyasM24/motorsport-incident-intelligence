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


_benchmark_service_instance: Optional[BenchmarkService] = None


def get_benchmark_service() -> BenchmarkService:
    """Retrieve or initialize the global BenchmarkService instance."""
    global _benchmark_service_instance
    if _benchmark_service_instance is None:
        _benchmark_service_instance = BenchmarkService()
    return _benchmark_service_instance
