"""Historical Incident Reconstruction Benchmark module."""

from app.benchmark.manifest import (
    BenchmarkManifest,
    BenchmarkTolerances,
    EvidenceAvailability,
    GroundTruthProvenance,
    HistoricalIncidentCase,
    InteractionCategory,
    VerificationStatus,
    get_verified_cases,
    leave_one_circuit_out_splits,
    leave_one_event_out_splits,
    leave_one_season_out_splits,
    load_benchmark_manifest,
    split_manifest_by_group,
)
from app.benchmark.evaluator import (
    BenchmarkSuiteReport,
    CaseEvaluationReport,
    FailureMode,
    HistoricalReconstructionEvaluator,
    MetricIndependenceCategory,
    MetricProvenanceAudit,
)
from app.benchmark.comparator import (
    ComparableIncidentMatch,
    ComparatorEvaluationReport,
    HistoricalCaseComparator,
)
from app.benchmark.service import (
    BenchmarkService,
    get_benchmark_service,
)

__all__ = [
    "BenchmarkManifest",
    "BenchmarkTolerances",
    "EvidenceAvailability",
    "GroundTruthProvenance",
    "HistoricalIncidentCase",
    "InteractionCategory",
    "VerificationStatus",
    "get_verified_cases",
    "leave_one_circuit_out_splits",
    "leave_one_event_out_splits",
    "leave_one_season_out_splits",
    "load_benchmark_manifest",
    "split_manifest_by_group",
    "BenchmarkSuiteReport",
    "CaseEvaluationReport",
    "FailureMode",
    "HistoricalReconstructionEvaluator",
    "MetricIndependenceCategory",
    "MetricProvenanceAudit",
    "ComparableIncidentMatch",
    "ComparatorEvaluationReport",
    "HistoricalCaseComparator",
    "BenchmarkService",
    "get_benchmark_service",
]
