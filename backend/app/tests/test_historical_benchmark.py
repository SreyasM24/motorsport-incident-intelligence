"""Comprehensive Automated Test Suite for Historical Incident Reconstruction Benchmark (Prompt 19).

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS:
    1. Zero Autonomous Guilt or Fault Determination: Validates that the benchmark only
       evaluates evidence reconstruction quality, never driver guilt, fault, or penalties.
    2. Epistemic Typing Verification: Enforces that statistical, ML, or documentary data
       cannot be upgraded to OBSERVED.
    3. Independent Observation Counting: Verifies that correlated metrics derived from
       the same telemetry stream count as 1 root origin.
    4. Deterministic Group Isolation: Validates that group partitioning prevents leakage.
    5. Non-Precedent Rule: Confirms comparable cases never treat past penalties as binding.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.benchmark.manifest import (
    BenchmarkManifest,
    BenchmarkTolerances,
    HistoricalIncidentCase,
    VerificationStatus,
    get_verified_cases,
    load_benchmark_manifest,
    split_manifest_by_group,
)
from app.benchmark.evaluator import (
    BenchmarkSuiteReport,
    CaseEvaluationReport,
    FailureMode,
    HistoricalReconstructionEvaluator,
)
from app.benchmark.comparator import HistoricalCaseComparator
from app.benchmark.service import get_benchmark_service
from app.evidence.synthesis.contracts import (
    ConsistencyStatus,
    DiscrepancySeverity,
    EvidenceItem,
    EvidenceStatus,
    EvidenceType,
)
from app.evidence.synthesis.lineage import LineageTracker


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def manifest() -> BenchmarkManifest:
    return load_benchmark_manifest()


@pytest.fixture(scope="module")
def evaluator(manifest: BenchmarkManifest) -> HistoricalReconstructionEvaluator:
    return HistoricalReconstructionEvaluator(manifest.tolerances)


# ==============================================================================
# 1. MANIFEST & SCHEMA INTEGRITY TESTS
# ==============================================================================

def test_manifest_loads_and_validates(manifest: BenchmarkManifest):
    """Verify that the benchmark manifest loads, parses, and satisfies all schema rules."""
    assert manifest.benchmark_version == "1.0.0"
    assert len(manifest.cases) >= 8
    assert manifest.tolerances.timestamp_absolute_error_seconds == 2.0
    assert manifest.tolerances.window_iou_threshold == 0.50


def test_manifest_case_schema_completeness(manifest: BenchmarkManifest):
    """Ensure every case includes mandatory authoritative documentary fields."""
    for case in manifest.cases:
        assert case.case_id.startswith("HIST-")
        assert case.series == "Formula 1"
        assert case.season in {2023, 2024}
        assert case.lap > 0
        assert len(case.driver_a) == 3
        assert len(case.driver_b) == 3
        assert case.incident_window.duration_seconds > 0
        assert case.documented_steward_outcome.epistemic_classification == "DOCUMENTARY"
        assert case.official_document is not None


def test_verified_vs_unverified_filtering(manifest: BenchmarkManifest):
    """Verify that unverified cases are identified and strictly excluded from scoring."""
    verified = get_verified_cases(manifest)
    unverified = [c for c in manifest.cases if c.verification_status == VerificationStatus.UNVERIFIED]

    assert len(verified) >= 7
    assert len(unverified) >= 1
    assert all(c.verification_status == VerificationStatus.VERIFIED for c in verified)
    assert any(c.verification_status == VerificationStatus.UNVERIFIED for c in unverified)


def test_deterministic_group_splitting_no_leakage(manifest: BenchmarkManifest):
    """Verify group-aware partitioning by circuit and driver pair has zero leakage."""
    circuit_splits = split_manifest_by_group(manifest, group_key="circuit")
    assert "Monza" in circuit_splits
    assert "Red Bull Ring" in circuit_splits

    # Verify no case appears in more than one partition
    all_case_ids: Set[str] = set()
    for grp_name, cases in circuit_splits.items():
        grp_ids = {c.case_id for c in cases}
        assert len(all_case_ids.intersection(grp_ids)) == 0, f"Leakage detected in group {grp_name}"
        all_case_ids.update(grp_ids)


# ==============================================================================
# 2. TIMESTAMP RECONSTRUCTION & WINDOW IOU TESTS
# ==============================================================================

def test_timestamp_evaluation_exact_match(evaluator: HistoricalReconstructionEvaluator):
    """Verify timestamp evaluation when reconstruction perfectly matches ground truth."""
    eval_res = evaluator.evaluate_timestamp(
        gt_start="2024-09-01T13:28:40.000Z",
        gt_end="2024-09-01T13:28:45.000Z",
        gt_peak="2024-09-01T13:28:42.500Z",
        rec_start="2024-09-01T13:28:40.000Z",
        rec_end="2024-09-01T13:28:45.000Z",
        rec_peak="2024-09-01T13:28:42.500Z",
    )
    assert eval_res.absolute_error_seconds == 0.0
    assert eval_res.window_iou == 1.0
    assert eval_res.within_tolerance is True


def test_timestamp_evaluation_out_of_tolerance(evaluator: HistoricalReconstructionEvaluator):
    """Verify timestamp evaluation correctly flags offsets exceeding predefined 2.0s tolerance."""
    eval_res = evaluator.evaluate_timestamp(
        gt_start="2024-09-01T13:28:40.000Z",
        gt_end="2024-09-01T13:28:45.000Z",
        gt_peak="2024-09-01T13:28:42.500Z",
        rec_start="2024-09-01T13:28:48.000Z",
        rec_end="2024-09-01T13:28:53.000Z",
        rec_peak="2024-09-01T13:28:50.500Z",
    )
    assert eval_res.absolute_error_seconds == 8.0
    assert eval_res.window_iou == 0.0
    assert eval_res.within_tolerance is False


# ==============================================================================
# 3. VEHICLE ASSOCIATION PRECISION & RECALL TESTS
# ==============================================================================

def test_vehicle_association_metrics(evaluator: HistoricalReconstructionEvaluator):
    """Verify precision, recall, and F1 calculation for vehicle pair identification."""
    # Perfect match
    perf = evaluator.evaluate_vehicles(["RIC", "HUL"], ["HUL", "RIC"])
    assert perf.pair_matched is True
    assert perf.precision == 1.0
    assert perf.recall == 1.0
    assert perf.f1_score == 1.0

    # Partial match (1 correct driver, 1 false positive)
    part = evaluator.evaluate_vehicles(["RIC", "HUL"], ["RIC", "NOR"])
    assert part.pair_matched is False
    assert part.precision == 0.5
    assert part.recall == 0.5
    assert part.f1_score == 0.5


# ==============================================================================
# 4. SPATIAL & KINEMATIC PLAUSIBILITY TESTS
# ==============================================================================

def test_spatial_telemetry_plausibility(evaluator: HistoricalReconstructionEvaluator):
    """Verify physical sanity bounds for reconstructed kinematics."""
    # Valid racing kinematics
    valid = evaluator.evaluate_spatial_telemetry(
        gap_meters=1.45,
        delta_brake=12.5,
        traj_dev=0.85,
        speed_kmh=265.0,
        lat_g=-3.2,
    )
    assert valid.all_spatial_checks_passed is True
    assert valid.gap_physically_plausible is True
    assert valid.speed_within_physical_bounds is True

    # Physically impossible kinematics (negative gap, extreme impossible speed)
    invalid = evaluator.evaluate_spatial_telemetry(
        gap_meters=-5.0,
        delta_brake=120.0,
        traj_dev=12.0,
        speed_kmh=520.0,
        lat_g=15.0,
    )
    assert invalid.all_spatial_checks_passed is False
    assert invalid.gap_physically_plausible is False
    assert invalid.speed_within_physical_bounds is False


# ==============================================================================
# 5. REFERENCE BASELINE SELECTION & CONTAMINATION PREVENTION TESTS
# ==============================================================================

def test_reference_baseline_contamination_check(evaluator: HistoricalReconstructionEvaluator):
    """Verify baseline selection rejects contaminated laps (incident, pit, invalid)."""
    # Pure clean laps
    clean_eval = evaluator.evaluate_reference_baseline(
        incident_lap=15,
        used_laps=[11, 12, 13, 14],
        pit_laps=[20],
        invalid_laps=[1],
    )
    assert clean_eval.baseline_status == "AVAILABLE"
    assert clean_eval.incident_lap_excluded is True
    assert clean_eval.sufficient_reference_data is True

    # Contaminated with incident lap
    contam_eval = evaluator.evaluate_reference_baseline(
        incident_lap=15,
        used_laps=[14, 15, 16],
        pit_laps=[],
        invalid_laps=[],
    )
    assert contam_eval.baseline_status == "INSUFFICIENT_REFERENCE_DATA"
    assert contam_eval.incident_lap_excluded is False


# ==============================================================================
# 6. EPISTEMIC INTEGRITY & UPGRADE DETECTION TESTS
# ==============================================================================

def test_epistemic_integrity_detects_illegal_upgrades(evaluator: HistoricalReconstructionEvaluator):
    """CRITICAL TEST: Verify that illegal epistemic upgrades are caught and flagged."""
    # Illegal upgrade: ML interaction model output marked as OBSERVED
    illegal_items = [
        EvidenceItem(
            evidence_id="EV-TEST-01",
            evidence_type=EvidenceType.ML_INTERACTION,
            source_layer="Interaction Anomaly Classifier",
            status=EvidenceStatus.OBSERVED,  # ILLEGAL: Model output cannot be observed sensor data!
            observation="ML classification probability 0.89",
            provenance="Classifier v1",
            parent_evidence_ids=[],
        ),
        EvidenceItem(
            evidence_id="EV-TEST-02",
            evidence_type=EvidenceType.REGULATION,
            source_layer="FIA Statute Index",
            status=EvidenceStatus.OBSERVED,  # ILLEGAL: Regulatory statutes are DOCUMENTARY, not OBSERVED!
            observation="Article 33.4",
            provenance="FIA Sporting Regulations",
            parent_evidence_ids=[],
        ),
    ]

    check = evaluator.check_epistemic_integrity(illegal_items)
    assert check.compliance_passed is False
    assert check.illegal_upgrades_detected == 2
    assert "Model-derived item classified as OBSERVED" in check.epistemic_upgrade_violations[0]


# ==============================================================================
# 7. LINEAGE TRACKING & DOUBLE-COUNTING PREVENTION TESTS
# ==============================================================================

def test_lineage_tracker_deduplicates_correlated_metrics():
    """Verify that multiple derived metrics from 1 telemetry stream count as 1 root origin."""
    items = [
        # Root origin
        EvidenceItem(
            evidence_id="EV-ROOT-TEL",
            evidence_type=EvidenceType.TELEMETRY,
            source_layer="FastF1 25Hz CAN-Bus",
            status=EvidenceStatus.OBSERVED,
            observation="Raw ECU Sensor Readings",
            provenance="FastF1 Stream",
            parent_evidence_ids=[],
        ),
        # Derived metric 1 (from root)
        EvidenceItem(
            evidence_id="EV-DERIVED-GAP",
            evidence_type=EvidenceType.OVERTAKE_GEOMETRY,
            source_layer="Spatial Geometry",
            status=EvidenceStatus.DERIVED,
            observation="Minimum Gap 1.45m",
            provenance="MII Spatial Engine",
            parent_evidence_ids=["EV-ROOT-TEL"],
        ),
        # Derived metric 2 (from root)
        EvidenceItem(
            evidence_id="EV-DERIVED-CLOSING",
            evidence_type=EvidenceType.TELEMETRY,
            source_layer="Differential Kinematics",
            status=EvidenceStatus.DERIVED,
            observation="Closing Speed 8.2 m/s",
            provenance="Kinematics Calculator",
            parent_evidence_ids=["EV-ROOT-TEL"],
        ),
        # Separate documentary root
        EvidenceItem(
            evidence_id="EV-DOC-REG",
            evidence_type=EvidenceType.REGULATION,
            source_layer="FIA Statutes",
            status=EvidenceStatus.DOCUMENTARY,
            observation="Article 33.4",
            provenance="FIA Rulebook",
            parent_evidence_ids=[],
        ),
    ]

    naive_count = len(items)
    root_count = LineageTracker.compute_independent_observation_count(items)

    assert naive_count == 4
    # The 3 telemetry items (1 raw + 2 derived) collapse to 1 root origin.
    # Total independent roots: 1 (telemetry) + 1 (regulation) = 2
    assert root_count == 2


# ==============================================================================
# 8. HISTORICAL COMPARATOR & PRECEDENT GUARDRAIL TESTS
# ==============================================================================

def test_historical_comparator_observable_similarity_only(manifest: BenchmarkManifest):
    """Verify comparable incident matching is based on physical dimensions, not penalties."""
    comparator = HistoricalCaseComparator(manifest)
    matches = comparator.find_comparable_incidents(query_case_id="HIST-2024-ITA-R-01", top_k=2)

    assert len(matches) > 0
    top_match = matches[0]
    assert top_match.observable_similarity_score > 0.0
    assert "minimum_gap_meters_range" in top_match.physical_dimensions
    assert top_match.documentary_context.epistemic_status == "DOCUMENTARY"
    assert "CRITICAL NON-ADJUDICATIVE NOTICE" in top_match.epistemic_warning


# ==============================================================================
# 9. SUITE-LEVEL BENCHMARK EXECUTION TESTS
# ==============================================================================

def test_run_benchmark_suite(evaluator: HistoricalReconstructionEvaluator, manifest: BenchmarkManifest):
    """Run full benchmark suite and verify multi-dimensional decoupled reporting."""
    suite_report = evaluator.evaluate_manifest(manifest)

    assert isinstance(suite_report, BenchmarkSuiteReport)
    assert suite_report.total_cases >= 8
    assert suite_report.verified_cases >= 7
    assert suite_report.unverified_excluded_cases >= 1
    assert suite_report.nominal_control_cases >= 3

    # Verify separate non-composite dimensional metrics
    assert suite_report.timestamp_reconstruction_accuracy_rate >= 0.85
    assert suite_report.vehicle_pair_match_accuracy >= 0.85
    assert suite_report.spatial_plausibility_rate >= 0.85
    assert suite_report.baseline_validity_rate >= 0.70
    assert suite_report.epistemic_typing_compliance_rate == 1.0
    assert suite_report.regulation_epistemic_purity_rate == 1.0

    # Ensure Lineage tracking demonstrates double-counting prevention
    assert suite_report.mean_root_independent_observations < suite_report.mean_naive_metrics


# ==============================================================================
# 10. API ENDPOINT INTEGRATION TESTS
# ==============================================================================

def test_api_benchmark_report_endpoint(client: TestClient):
    """Verify GET /api/v1/analysis/benchmark/historical-incidents returns full suite report."""
    res = client.get("/api/v1/analysis/benchmark/historical-incidents")
    assert res.status_code == 200
    data = res.json()
    assert data["benchmarkVersion"] == "1.0.0"
    assert data["totalCases"] >= 8
    assert data["verifiedCases"] >= 7
    assert "circuitsEvaluated" in data
    assert "caseReports" in data


def test_api_benchmark_single_case_endpoint(client: TestClient):
    """Verify GET /api/v1/analysis/benchmark/historical-incidents/{case_id}."""
    res = client.get("/api/v1/analysis/benchmark/historical-incidents/HIST-2024-ITA-R-01")
    assert res.status_code == 200
    data = res.json()
    assert data["caseId"] == "HIST-2024-ITA-R-01"
    assert data["verificationStatus"] == "VERIFIED"
    assert data["timestampEval"]["withinTolerance"] is True
    assert data["vehicleEval"]["pairMatched"] is True


def test_api_benchmark_single_case_not_found(client: TestClient):
    """Verify 404 for unknown case ID."""
    res = client.get("/api/v1/analysis/benchmark/historical-incidents/NONEXISTENT-CASE")
    assert res.status_code == 404


def test_api_benchmark_comparable_incidents_endpoint(client: TestClient):
    """Verify GET /api/v1/analysis/benchmark/historical-incidents/{case_id}/comparable."""
    res = client.get("/api/v1/analysis/benchmark/historical-incidents/HIST-2024-ITA-R-01/comparable?top_k=2")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) <= 2
    assert "epistemicWarning" in data[0]
    assert data[0]["documentaryContext"]["epistemicStatus"] == "DOCUMENTARY"
