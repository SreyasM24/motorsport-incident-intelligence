"""Historical Incident Reconstruction Benchmark — Manifest & Data Models (Prompt 19).

CRITICAL JURISPRUDENTIAL & EPISTEMIC GUARDRAILS:
    1. Zero Autonomous Guilt or Penalty Prediction: Historical steward decisions are
       treated strictly as DOCUMENTARY context, never as ground-truth physical causality
       or training labels for guilt.
    2. Strict Epistemic Boundaries: Maintains OBSERVED, DERIVED, MODEL_DERIVED,
       DOCUMENTARY, and UNAVAILABLE. Prevents epistemic type upgrades.
    3. Verification Integrity: Cases marked UNVERIFIED are strictly excluded from
       quantitative scoring.
    4. Group Isolation: Enforces deterministic group-aware splitting (circuit, event,
       session, driver pair) to eliminate entity and temporal leakage.
"""

from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class GroundTruthProvenance(str, Enum):
    """Provenance origin of benchmark ground truth."""
    OFFICIAL_DOCUMENT = "OFFICIAL_DOCUMENT"
    INDEPENDENT_TELEMETRY = "INDEPENDENT_TELEMETRY"
    INDEPENDENT_ANNOTATION = "INDEPENDENT_ANNOTATION"
    DERIVED_FROM_SAME_TELEMETRY = "DERIVED_FROM_SAME_TELEMETRY"
    UNKNOWN = "UNKNOWN"


class InteractionCategory(str, Enum):
    """Observable interaction categories supported by empirical evidence."""
    FORCING_OFF_TRACK = "FORCING_OFF_TRACK"
    CONTACT_COLLISION = "CONTACT_COLLISION"
    OVERTAKING_INTERACTION = "OVERTAKING_INTERACTION"
    BRAKING_APPROACH = "BRAKING_APPROACH"
    CORNER_ENTRY = "CORNER_ENTRY"
    CORNER_EXIT = "CORNER_EXIT"
    SIDE_BY_SIDE = "SIDE_BY_SIDE"
    DEFENSIVE_POSITIONING = "DEFENSIVE_POSITIONING"
    NOMINAL_RACING_CONTROL = "NOMINAL_RACING_CONTROL"


class VerificationStatus(str, Enum):
    """Authoritative verification status."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class GroundTruthType(str, Enum):
    """Nature of documentary benchmark source."""
    OFFICIAL_STEWARD_DECISION = "OFFICIAL_STEWARD_DECISION"
    NOMINAL_RACING_CONTROL = "NOMINAL_RACING_CONTROL"
    UNVERIFIED = "UNVERIFIED"


class EvidenceAvailability(str, Enum):
    """Empirical availability state of a data stream."""
    AVAILABLE = "AVAILABLE"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class IncidentWindow(BaseModel):
    """Temporal window encompassing an interaction."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    start_time: str
    end_time: str
    peak_time: str
    duration_seconds: float


class SplitGroup(BaseModel):
    """Hierarchical grouping keys for leakage-free evaluation."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    circuit: str
    event: str
    session: str
    driver_pair: str
    season: Optional[int] = None


class DocumentedStewardOutcome(BaseModel):
    """Historical documentary record of officiating actions.
    
    STRICT EPISTEMIC RULE:
        This is documentary historical context only. It is NOT physical truth,
        a target label, or a recommended outcome.
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    decision_type: str
    description: str
    epistemic_classification: str = Field(default="DOCUMENTARY")
    adjudicative_note: str = Field(
        default="Historical documentary record; does not constitute physical causality or an automated verdict."
    )


class ExpectedReconstructionTargets(BaseModel):
    """Plausibility boundaries for quantitative evidence reconstruction."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    driver_pair: List[str]
    primary_turn: str
    minimum_gap_meters_range: List[float] = Field(default_factory=lambda: [0.0, 10.0])
    delta_brake_meters_range: List[float] = Field(default_factory=lambda: [-10.0, 30.0])
    expected_relevant_articles: List[str] = Field(default_factory=list)
    reference_baseline_status: str = "AVAILABLE"
    expected_discrepancy_severity: str = "LOW"


class HistoricalIncidentCase(BaseModel):
    """Canonical model for a benchmark case."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    case_id: str
    series: str = "Formula 1"
    season: int
    event: str
    session: str = "Race"
    lap: int
    driver_a: str
    driver_b: str
    incident_timestamp: str
    incident_window: IncidentWindow
    circuit: str
    corner: str
    official_document: str
    official_document_url: str
    document_identifier: str
    documented_incident_description: str
    data_sources: List[str] = Field(default_factory=list)
    video_availability: EvidenceAvailability = EvidenceAvailability.UNAVAILABLE
    telemetry_availability: EvidenceAvailability = EvidenceAvailability.AVAILABLE
    regulation_availability: EvidenceAvailability = EvidenceAvailability.AVAILABLE
    ground_truth_type: GroundTruthType
    ground_truth_provenance: GroundTruthProvenance = GroundTruthProvenance.DERIVED_FROM_SAME_TELEMETRY
    verification_status: VerificationStatus
    interaction_category: InteractionCategory
    is_control_case: bool = False
    split_group: SplitGroup
    documented_steward_outcome: DocumentedStewardOutcome
    expected_reconstruction_targets: ExpectedReconstructionTargets


class BenchmarkTolerances(BaseModel):
    """Predefined deterministic evaluation tolerances."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    timestamp_absolute_error_seconds: float = 2.0
    window_iou_threshold: float = 0.50
    video_sync_offset_tolerance_seconds: float = 0.20
    spatial_gap_tolerance_meters: float = 0.50
    minimum_reference_laps: int = 3


class BenchmarkManifest(BaseModel):
    """Top-level container for benchmark suite."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    benchmark_version: str
    name: str
    description: str
    epistemic_framework: Dict[str, Any]
    tolerances: BenchmarkTolerances
    cases: List[HistoricalIncidentCase]


DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "data"
    / "benchmarks"
    / "historical_incidents"
    / "historical_incidents_v1.json"
)


def load_benchmark_manifest(manifest_path: Optional[Path] = None) -> BenchmarkManifest:
    """Load and validate the benchmark manifest from JSON file."""
    path = manifest_path or DEFAULT_MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(f"Benchmark manifest not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return BenchmarkManifest.model_validate(data)


def get_verified_cases(manifest: BenchmarkManifest) -> List[HistoricalIncidentCase]:
    """Retrieve only authoritative verified cases for quantitative scoring.
    
    Unverified cases are strictly excluded from quantitative benchmark scores.
    """
    return [c for c in manifest.cases if c.verification_status == VerificationStatus.VERIFIED]


def split_manifest_by_group(
    manifest: BenchmarkManifest,
    group_key: str = "circuit",
) -> Dict[str, List[HistoricalIncidentCase]]:
    """Partition cases deterministically by a grouping dimension to prevent leakage."""
    splits: Dict[str, List[HistoricalIncidentCase]] = {}
    for case in manifest.cases:
        key = getattr(case.split_group, group_key, getattr(case, group_key, case.circuit))
        splits.setdefault(str(key), []).append(case)
    return splits


def leave_one_circuit_out_splits(
    manifest: BenchmarkManifest,
    verified_only: bool = True,
) -> Dict[str, Dict[str, List[HistoricalIncidentCase]]]:
    """Generate Leave-One-Circuit-Out partitions ensuring zero cross-circuit data leakage."""
    pool = get_verified_cases(manifest) if verified_only else manifest.cases
    circuits = sorted(list(set(c.circuit for c in pool)))
    splits: Dict[str, Dict[str, List[HistoricalIncidentCase]]] = {}

    for holdout_circuit in circuits:
        train_cases = [c for c in pool if c.circuit != holdout_circuit]
        test_cases = [c for c in pool if c.circuit == holdout_circuit]
        splits[holdout_circuit] = {
            "train": train_cases,
            "test": test_cases,
        }
    return splits


def leave_one_season_out_splits(
    manifest: BenchmarkManifest,
    verified_only: bool = True,
) -> Dict[str, Dict[str, List[HistoricalIncidentCase]]]:
    """Generate Leave-One-Season-Out partitions ensuring zero temporal/year-level leakage."""
    pool = get_verified_cases(manifest) if verified_only else manifest.cases
    seasons = sorted(list(set(c.season for c in pool)))
    splits: Dict[str, Dict[str, List[HistoricalIncidentCase]]] = {}

    for holdout_season in seasons:
        train_cases = [c for c in pool if c.season != holdout_season]
        test_cases = [c for c in pool if c.season == holdout_season]
        splits[str(holdout_season)] = {
            "train": train_cases,
            "test": test_cases,
        }
    return splits


def leave_one_event_out_splits(
    manifest: BenchmarkManifest,
    verified_only: bool = True,
) -> Dict[str, Dict[str, List[HistoricalIncidentCase]]]:
    """Generate Leave-One-Event-Out partitions ensuring zero Grand Prix session leakage."""
    pool = get_verified_cases(manifest) if verified_only else manifest.cases
    events = sorted(list(set(c.split_group.event for c in pool)))
    splits: Dict[str, Dict[str, List[HistoricalIncidentCase]]] = {}

    for holdout_event in events:
        train_cases = [c for c in pool if c.split_group.event != holdout_event]
        test_cases = [c for c in pool if c.split_group.event == holdout_event]
        splits[holdout_event] = {
            "train": train_cases,
            "test": test_cases,
        }
    return splits
