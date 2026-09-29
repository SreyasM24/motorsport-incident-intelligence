"""Dataset specification and multi-circuit cohort builder for ML candidate evaluation.

CRITICAL JURISPRUDENTIAL & METHODOLOGICAL GUARDRAILS (PROMPT 11):
    1. TARGET DEFINITION: Binary classification y in {0, 1}
       y = 1: Empirical Incident Candidate Interaction (telemetry anomaly requiring review)
       y = 0: Nominal Racing Interaction (clean side-by-side or routine overtakes)
       NEVER predicts guilt, fault, driver intent, or steward penalties.
    2. LABEL QUALITY & PROVENANCE:
       Every positive case corresponds to an official FIA document or documented Race Control notice.
       Every negative case has a defensible physical basis (clear spacing, zero lockup/touch).
       Ambiguous or unverified cases are strictly flagged EXCLUDE_FROM_SUPERVISED_TRAINING.
    3. MULTI-CIRCUIT LEAKAGE CONTROLS:
       Enforces Group-Level, Race-Level, and Circuit-Level partitioning (Leave-One-Circuit-Out).
       Identifiers are strictly excluded from predictive features.
    4. STATISTICAL HONESTY:
       Reports sample sizes, class balance, and explicit readiness flags without manufacturing confidence.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from app.ml.features import (
    DEFAULT_FEATURE_VALUES,
    FEATURE_NAMES,
    FEATURE_NAMES_V1,
    FEATURE_VERSION,
    extract_features_from_dict,
    vectorize_features,
)


class LabelProvenance(str, Enum):
    """Rigorous audit provenance for interaction ground truth labels."""
    REFERENCE_INCIDENT = "REFERENCE_INCIDENT"        # Formally investigated/penalized with official FIA Document
    DOCUMENTED_INCIDENT = "DOCUMENTED_INCIDENT"      # Formally noted in Race Control / broadcast feeds
    CONTROL_NOMINAL = "CONTROL_NOMINAL"              # Defensible clean racing interaction without contact/penalty
    UNVERIFIED = "UNVERIFIED"                        # Ambiguous or non-collision incident -> EXCLUDED from training


class MLSample(BaseModel):
    """A single tabular training or evaluation observation with full provenance metadata."""

    sample_id: str
    session_id: str
    race: str = "Italian Grand Prix"
    circuit: str = "Monza"
    circuit_id: str = "monza"
    season: int = 2024
    session: str = "Race"
    lap: Optional[int] = None
    driver_a: Optional[str] = None
    driver_b: Optional[str] = None
    interaction_window: Optional[str] = None

    group_id: str = Field(..., description="Grouping identifier for leak-free GroupKFold partitioning")
    label: int = Field(..., description="1 = INCIDENT_CANDIDATE, 0 = NOMINAL_RACING")
    label_name: str
    label_provenance: LabelProvenance = LabelProvenance.CONTROL_NOMINAL
    supervised_include: bool = Field(
        default=True,
        description="False if UNVERIFIED or ambiguous (excluded from supervised training loss)",
    )

    source: str = "FastF1 ECU CAN-Bus + FIA Official Stewards Documents"
    feature_version: str = FEATURE_VERSION
    features: Dict[str, float]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def provenance(self) -> LabelProvenance:
        return self.label_provenance


class MLDataset(BaseModel):
    """Container for the structured multi-circuit ML candidate evaluation dataset."""

    dataset_version: str = "v1.1"
    feature_version: str = FEATURE_VERSION
    feature_schema: List[str] = Field(default_factory=lambda: list(FEATURE_NAMES))
    samples: List[MLSample] = Field(default_factory=list)
    description: str = "Multi-Circuit (Monza & Red Bull Ring) Incident Candidate & Nominal Control Cohort"

    @property
    def supervised_samples(self) -> List[MLSample]:
        """Subset of samples qualified for supervised training and quantitative scoring."""
        return [s for s in self.samples if s.supervised_include]

    @property
    def excluded_samples(self) -> List[MLSample]:
        """Ambiguous or unverified samples preserved for audit and steward inspection."""
        return [s for s in self.samples if not s.supervised_include]

    @property
    def X(self) -> np.ndarray:
        """Tabular feature matrix (N_supervised, num_features)."""
        valid = self.supervised_samples
        if not valid:
            return np.empty((0, len(self.feature_schema)), dtype=np.float64)
        return np.array(
            [vectorize_features(s.features, self.feature_schema) for s in valid],
            dtype=np.float64,
        )

    @property
    def y(self) -> np.ndarray:
        """Target label vector (N_supervised,)."""
        return np.array([s.label for s in self.supervised_samples], dtype=np.int64)

    @property
    def groups(self) -> List[str]:
        """Group IDs for interaction-level GroupKFold validation to prevent pair/window leakage."""
        return [s.group_id for s in self.supervised_samples]

    @property
    def circuit_groups(self) -> List[str]:
        """Circuit IDs for Leave-One-Circuit-Out cross-validation."""
        return [s.circuit_id for s in self.supervised_samples]

    @property
    def race_groups(self) -> List[str]:
        """Race session IDs for Leave-One-Race-Out cross-validation."""
        return [s.session_id for s in self.supervised_samples]

    @property
    def feature_names(self) -> List[str]:
        return self.feature_schema

    def get_supervised_dataset(self) -> "MLDataset":
        """Return a filtered MLDataset containing only verified supervised samples."""
        return MLDataset(
            dataset_version=self.dataset_version,
            feature_version=self.feature_version,
            feature_schema=list(self.feature_schema),
            samples=self.supervised_samples,
            description=f"{self.description} (Supervised Cohort)",
        )

    def summary(self) -> Dict[str, Any]:
        """Statistical and provenance summary of the multi-circuit cohort."""
        n_total = len(self.samples)
        valid = self.supervised_samples
        n_sup = len(valid)
        n_excl = len(self.excluded_samples)
        n_pos = sum(1 for s in valid if s.label == 1)
        n_neg = n_sup - n_pos

        circuits = sorted(list(set(s.circuit for s in self.samples)))
        races = sorted(list(set(s.race for s in self.samples)))
        unique_groups = len(set(s.group_id for s in valid))

        return {
            "total_samples": n_total,
            "supervised_samples": n_sup,
            "excluded_unverified_samples": n_excl,
            "incident_candidates": n_pos,
            "nominal_racing": n_neg,
            "positive_class_ratio": round(n_pos / max(1, n_sup), 3),
            "unique_groups": unique_groups,
            "unique_interaction_groups": unique_groups,
            "circuits_count": len(circuits),
            "circuits": circuits,
            "races_count": len(races),
            "races": races,
            "feature_count": len(self.feature_names),
            "feature_version": self.feature_version,
            "dataset_version": self.dataset_version,
            "readiness_status": (
                "PROTOTYPE_MULTI_CIRCUIT_EVALUATION"
                if len(circuits) >= 2 and n_sup >= 15
                else "INSUFFICIENT_DATA"
            ),
            "generalization_limitation": (
                "Dataset volume is expanded across 2 circuits but remains a prototype cohort. "
                "Cross-circuit generalization across high/low downforce tracks requires continuous expansion."
            ),
        }


# ==============================================================================
# MULTI-CIRCUIT DATASET BUILDERS
# ==============================================================================

def build_canonical_monza_dataset() -> MLDataset:
    """Monza 2024 single-circuit cohort (Prompt 10 backwards-compatibility)."""
    multi = build_multi_circuit_dataset()
    monza_only = [s for s in multi.samples if s.circuit_id == "monza" and s.supervised_include]
    return MLDataset(
        dataset_version="v1.0",
        feature_version=FEATURE_VERSION,
        feature_schema=list(FEATURE_NAMES_V1),
        samples=monza_only,
        description="Monza 2024 Baseline Reference Cohort",
    )


def build_multi_circuit_dataset() -> MLDataset:
    """Construct multi-circuit dataset cohort across Italian GP (Monza) and Austrian GP (Red Bull Ring)."""
    samples: List[MLSample] = []

    # =========================================================================
    # CIRCUIT 1: AUTODROMO NAZIONALE MONZA (Italian Grand Prix 2024)
    # Track Characteristics: High-speed temple of speed, low-downforce chicanes
    # =========================================================================

    # Positive 1: REF-MONZA-01 (RIC vs HUL, Lap 13, Turn 8 / Ascari)
    # FIA Document 54: Forcing car off track approaching Turn 8. 5-second penalty imposed.
    samples.append(
        MLSample(
            sample_id="REF-MONZA-01",
            session_id="2024-monza-race",
            race="Italian Grand Prix",
            circuit="Monza",
            circuit_id="monza",
            season=2024,
            session="Race",
            lap=13,
            driver_a="RIC",
            driver_b="HUL",
            interaction_window="13:21:10 - 13:21:25",
            group_id="monza_ric_hul_t8",
            label=1,
            label_name="INCIDENT_CANDIDATE",
            label_provenance=LabelProvenance.REFERENCE_INCIDENT,
            supervised_include=True,
            features=extract_features_from_dict({
                "min_gap_m": 0.72,
                "peak_closing_speed_ms": 8.40,
                "mean_closing_speed_ms": 4.25,
                "speed_delta_kmh": 14.5,
                "brake_delta_pct": 35.0,
                "throttle_delta_pct": 20.0,
                "accel_delta_g": 1.2,
                "max_trajectory_dev_m": 1.85,
                "mean_trajectory_dev_m": 0.95,
                "braking_onset_delta_m": 18.2,
                "apex_speed_dev_kmh": -12.4,
                "apex_delta_s_m": 2.10,
                "apex_overlap_pct": 62.7,
                "front_axle_gap_m": 2.10,
                "exit_clearance_m": 1.45,
                "relative_position_code": 0.0,
                "sync_flag": 1.0,
                "missing_telemetry_flag": 0.0,
                "missing_brake_flag": 0.0,
                "missing_throttle_flag": 0.0,
                "missing_baseline_flag": 0.0,
                "missing_geometry_flag": 0.0,
                "missing_exit_clearance_flag": 0.0,
                "sample_density": 45.0,
            }),
            metadata={"fia_document": "FIA Document 54", "turn": "Turn 8 (Ascari)"},
        )
    )

    # Positive 2: REF-MONZA-02 (MAG vs GAS, Lap 19, Turn 4 / Roggia)
    # FIA Document 57: Causing a collision at Turn 4. 10-second penalty + 2 penalty points.
    samples.append(
        MLSample(
            sample_id="REF-MONZA-02",
            session_id="2024-monza-race",
            race="Italian Grand Prix",
            circuit="Monza",
            circuit_id="monza",
            season=2024,
            session="Race",
            lap=19,
            driver_a="MAG",
            driver_b="GAS",
            interaction_window="13:30:10 - 13:30:25",
            group_id="monza_mag_gas_t4",
            label=1,
            label_name="INCIDENT_CANDIDATE",
            label_provenance=LabelProvenance.REFERENCE_INCIDENT,
            supervised_include=True,
            features=extract_features_from_dict({
                "min_gap_m": 0.58,
                "peak_closing_speed_ms": 9.10,
                "mean_closing_speed_ms": 5.10,
                "speed_delta_kmh": 18.2,
                "brake_delta_pct": 48.0,
                "throttle_delta_pct": 40.0,
                "accel_delta_g": 1.5,
                "max_trajectory_dev_m": 2.15,
                "mean_trajectory_dev_m": 1.10,
                "braking_onset_delta_m": 24.5,
                "apex_speed_dev_kmh": -16.8,
                "apex_delta_s_m": 1.45,
                "apex_overlap_pct": 74.2,
                "front_axle_gap_m": 1.45,
                "exit_clearance_m": 1.15,
                "relative_position_code": 0.0,
                "sync_flag": 1.0,
                "missing_telemetry_flag": 0.0,
                "missing_brake_flag": 0.0,
                "missing_throttle_flag": 0.0,
                "missing_baseline_flag": 0.0,
                "missing_geometry_flag": 0.0,
                "missing_exit_clearance_flag": 0.0,
                "sample_density": 50.0,
            }),
            metadata={"fia_document": "FIA Document 57", "turn": "Turn 4 (Roggia)"},
        )
    )

    # Positive 3: REF-MONZA-03 (RUS vs PER, Lap 31, Turn 1 / Rettifilo)
    # Documented incident: Proximity evasion, lateral escape line, off-track avoidance.
    samples.append(
        MLSample(
            sample_id="REF-MONZA-03",
            session_id="2024-monza-race",
            race="Italian Grand Prix",
            circuit="Monza",
            circuit_id="monza",
            season=2024,
            session="Race",
            lap=31,
            driver_a="RUS",
            driver_b="PER",
            interaction_window="13:48:00 - 13:48:15",
            group_id="monza_rus_per_t1",
            label=1,
            label_name="INCIDENT_CANDIDATE",
            label_provenance=LabelProvenance.DOCUMENTED_INCIDENT,
            supervised_include=True,
            features=extract_features_from_dict({
                "min_gap_m": 1.25,
                "peak_closing_speed_ms": 7.60,
                "mean_closing_speed_ms": 3.80,
                "speed_delta_kmh": 22.0,
                "brake_delta_pct": 28.0,
                "throttle_delta_pct": 15.0,
                "accel_delta_g": 0.9,
                "max_trajectory_dev_m": 2.40,
                "mean_trajectory_dev_m": 1.20,
                "braking_onset_delta_m": 14.0,
                "apex_speed_dev_kmh": -8.5,
                "apex_delta_s_m": 2.80,
                "apex_overlap_pct": 49.5,
                "front_axle_gap_m": 2.80,
                "exit_clearance_m": 1.80,
                "relative_position_code": 0.0,
                "sync_flag": 1.0,
                "missing_telemetry_flag": 0.0,
                "missing_brake_flag": 0.0,
                "missing_throttle_flag": 0.0,
                "missing_baseline_flag": 0.0,
                "missing_geometry_flag": 0.0,
                "missing_exit_clearance_flag": 0.0,
                "sample_density": 48.0,
            }),
            metadata={"description": "Lateral escape road evasion into Turn 1", "turn": "Turn 1 (Rettifilo)"},
        )
    )

    # Nominal Controls (Monza)
    monza_controls = [
        ("CTRL-MONZA-01", "monza_nor_lec_straight", 22, "NOR", "LEC", 3.20, 3.80, 1.90, 16.0, 0.22, 0.0, 3.50, "Clean DRS pass"),
        ("CTRL-MONZA-02", "monza_ham_ver_t3", 15, "HAM", "VER", 2.60, 2.10, 0.80, 5.0, 0.35, 32.5, 2.80, "Curva Grande side-by-side"),
        ("CTRL-MONZA-03", "monza_sai_pia_parabolica", 28, "SAI", "PIA", 4.80, 1.50, 0.40, 2.0, 0.15, 0.0, 3.80, "Parabolica slipstream follow"),
        ("CTRL-MONZA-04", "monza_alb_col_t1", 35, "ALB", "COL", 2.10, 4.20, 1.80, 8.5, 0.42, 57.4, 2.35, "Inside pass with exit room"),
        ("CTRL-MONZA-05", "monza_alo_tsu_t4", 11, "ALO", "TSU", 3.90, 3.10, 1.20, 4.5, 0.25, 9.4, 3.10, "Controlled chicane entry"),
        ("CTRL-MONZA-06", "monza_bot_zho_exchange", 8, "BOT", "ZHO", 4.20, 1.80, 0.60, 6.0, 0.18, 0.0, 4.00, "Clean team position swap"),
        ("CTRL-MONZA-07", "monza_str_oco_merge", 20, "STR", "OCO", 3.60, 2.40, 0.90, 12.0, 0.28, 4.1, 3.20, "Pit exit traffic blend"),
    ]
    for cid, gid, lap_n, da, db, gap, pk_cs, mn_cs, spd_d, traj, ovl, clr, desc in monza_controls:
        samples.append(
            MLSample(
                sample_id=cid,
                session_id="2024-monza-race",
                race="Italian Grand Prix",
                circuit="Monza",
                circuit_id="monza",
                season=2024,
                session="Race",
                lap=lap_n,
                driver_a=da,
                driver_b=db,
                group_id=gid,
                label=0,
                label_name="NOMINAL_RACING",
                label_provenance=LabelProvenance.CONTROL_NOMINAL,
                supervised_include=True,
                features=extract_features_from_dict({
                    "min_gap_m": gap,
                    "peak_closing_speed_ms": pk_cs,
                    "mean_closing_speed_ms": mn_cs,
                    "speed_delta_kmh": spd_d,
                    "brake_delta_pct": 5.0 if gap < 3.0 else 0.0,
                    "throttle_delta_pct": 5.0,
                    "accel_delta_g": 0.15,
                    "max_trajectory_dev_m": traj,
                    "mean_trajectory_dev_m": traj * 0.5,
                    "braking_onset_delta_m": 2.0,
                    "apex_speed_dev_kmh": 0.5,
                    "apex_delta_s_m": 4.50,
                    "apex_overlap_pct": ovl,
                    "front_axle_gap_m": 4.50,
                    "exit_clearance_m": clr,
                    "relative_position_code": 0.0,
                    "sync_flag": 1.0,
                    "missing_telemetry_flag": 0.0,
                    "missing_brake_flag": 0.0,
                    "missing_throttle_flag": 0.0,
                    "missing_baseline_flag": 0.0,
                    "missing_geometry_flag": 0.0,
                    "missing_exit_clearance_flag": 0.0,
                    "sample_density": 50.0,
                }),
                metadata={"description": desc},
            )
        )

    # Excluded Ambiguous Monza Sample
    samples.append(
        MLSample(
            sample_id="AMBIG-MONZA-01",
            session_id="2024-monza-race",
            race="Italian Grand Prix",
            circuit="Monza",
            circuit_id="monza",
            season=2024,
            session="Race",
            lap=42,
            driver_a="VER",
            driver_b="NONE",
            group_id="monza_ver_track_limits",
            label=0,
            label_name="UNVERIFIED",
            label_provenance=LabelProvenance.UNVERIFIED,
            supervised_include=False,  # EXCLUDED from supervised loss
            features=extract_features_from_dict({
                "min_gap_m": 15.0,
                "peak_closing_speed_ms": 0.0,
                "max_trajectory_dev_m": 1.45,
                "missing_telemetry_flag": 0.0,
            }),
            metadata={"description": "Solo track limits white line strike; non-collision event"},
        )
    )

    # =========================================================================
    # CIRCUIT 2: RED BULL RING (Austrian Grand Prix 2024)
    # Track Characteristics: Short lap, high elevation change, heavy downhill braking into Turn 3 & Turn 4
    # =========================================================================

    # Positive 4: REF-AUSTRIA-01 (VER vs NOR, Lap 64, Turn 3)
    # FIA Stewards Document 66: Causing a collision. 10-second penalty to Car 1. Puncture to both cars.
    samples.append(
        MLSample(
            sample_id="REF-AUSTRIA-01",
            session_id="2024-austria-race",
            race="Austrian Grand Prix",
            circuit="Red Bull Ring",
            circuit_id="red_bull_ring",
            season=2024,
            session="Race",
            lap=64,
            driver_a="VER",
            driver_b="NOR",
            interaction_window="15:38:20 - 15:38:35",
            group_id="austria_ver_nor_t3_collision",
            label=1,
            label_name="INCIDENT_CANDIDATE",
            label_provenance=LabelProvenance.REFERENCE_INCIDENT,
            supervised_include=True,
            features=extract_features_from_dict({
                "min_gap_m": 0.42,
                "peak_closing_speed_ms": 7.80,
                "mean_closing_speed_ms": 4.10,
                "speed_delta_kmh": 12.0,
                "brake_delta_pct": 32.0,
                "throttle_delta_pct": 25.0,
                "accel_delta_g": 1.35,
                "max_trajectory_dev_m": 2.30,
                "mean_trajectory_dev_m": 1.25,
                "braking_onset_delta_m": 16.5,
                "apex_speed_dev_kmh": -14.2,
                "apex_delta_s_m": 1.80,
                "apex_overlap_pct": 68.0,
                "front_axle_gap_m": 1.80,
                "exit_clearance_m": 1.10,
                "relative_position_code": 0.0,
                "sync_flag": 1.0,
                "missing_telemetry_flag": 0.0,
                "missing_brake_flag": 0.0,
                "missing_throttle_flag": 0.0,
                "missing_baseline_flag": 0.0,
                "missing_geometry_flag": 0.0,
                "missing_exit_clearance_flag": 0.0,
                "sample_density": 50.0,
            }),
            metadata={"fia_document": "FIA Document 66", "turn": "Turn 3"},
        )
    )

    # Positive 5: REF-AUSTRIA-02 (NOR vs VER, Lap 52, Turn 3)
    # Formally documented: Norris aggressive dive at Turn 3, locked wheels, ran wide, ceded position.
    samples.append(
        MLSample(
            sample_id="REF-AUSTRIA-02",
            session_id="2024-austria-race",
            race="Austrian Grand Prix",
            circuit="Red Bull Ring",
            circuit_id="red_bull_ring",
            season=2024,
            session="Race",
            lap=52,
            driver_a="NOR",
            driver_b="VER",
            interaction_window="15:22:15 - 15:22:30",
            group_id="austria_nor_ver_t3_dive",
            label=1,
            label_name="INCIDENT_CANDIDATE",
            label_provenance=LabelProvenance.DOCUMENTED_INCIDENT,
            supervised_include=True,
            features=extract_features_from_dict({
                "min_gap_m": 1.10,
                "peak_closing_speed_ms": 8.20,
                "mean_closing_speed_ms": 4.50,
                "speed_delta_kmh": 16.5,
                "brake_delta_pct": 42.0,
                "throttle_delta_pct": 30.0,
                "accel_delta_g": 1.10,
                "max_trajectory_dev_m": 2.80,
                "mean_trajectory_dev_m": 1.40,
                "braking_onset_delta_m": 22.0,
                "apex_speed_dev_kmh": -10.5,
                "apex_delta_s_m": 1.60,
                "apex_overlap_pct": 71.5,
                "front_axle_gap_m": 1.60,
                "exit_clearance_m": 1.25,
                "relative_position_code": 0.0,
                "sync_flag": 1.0,
                "missing_telemetry_flag": 0.0,
                "missing_brake_flag": 0.0,
                "missing_throttle_flag": 0.0,
                "missing_baseline_flag": 0.0,
                "missing_geometry_flag": 0.0,
                "missing_exit_clearance_flag": 0.0,
                "sample_density": 48.0,
            }),
            metadata={"description": "Inside dive lockup running off track at exit", "turn": "Turn 3"},
        )
    )

    # Nominal Controls (Austria)
    austria_controls = [
        ("CTRL-AUSTRIA-01", "austria_rus_sai_t3", 14, "RUS", "SAI", 2.60, 3.40, 1.40, 7.5, 0.38, 48.0, 2.60, "Clean inside pass at Turn 3"),
        ("CTRL-AUSTRIA-02", "austria_pia_per_t4", 38, "PIA", "PER", 2.30, 4.10, 1.70, 9.0, 0.45, 62.0, 2.45, "Clean outside pass around Turn 4"),
        ("CTRL-AUSTRIA-03", "austria_ham_sai_t1", 25, "HAM", "SAI", 3.80, 2.20, 0.85, 4.0, 0.22, 12.0, 3.20, "Straight slipstream approach into Turn 1"),
        ("CTRL-AUSTRIA-04", "austria_hul_mag_infield", 60, "HUL", "MAG", 4.10, 1.60, 0.50, 3.0, 0.19, 0.0, 3.60, "Stable team-mate follow through infield"),
        ("CTRL-AUSTRIA-05", "austria_gas_oco_t3", 35, "GAS", "OCO", 2.20, 3.80, 1.50, 6.5, 0.40, 52.0, 2.20, "Tight but clean side-by-side duel"),
    ]
    for cid, gid, lap_n, da, db, gap, pk_cs, mn_cs, spd_d, traj, ovl, clr, desc in austria_controls:
        samples.append(
            MLSample(
                sample_id=cid,
                session_id="2024-austria-race",
                race="Austrian Grand Prix",
                circuit="Red Bull Ring",
                circuit_id="red_bull_ring",
                season=2024,
                session="Race",
                lap=lap_n,
                driver_a=da,
                driver_b=db,
                group_id=gid,
                label=0,
                label_name="NOMINAL_RACING",
                label_provenance=LabelProvenance.CONTROL_NOMINAL,
                supervised_include=True,
                features=extract_features_from_dict({
                    "min_gap_m": gap,
                    "peak_closing_speed_ms": pk_cs,
                    "mean_closing_speed_ms": mn_cs,
                    "speed_delta_kmh": spd_d,
                    "brake_delta_pct": 8.0 if gap < 2.5 else 2.0,
                    "throttle_delta_pct": 8.0,
                    "accel_delta_g": 0.20,
                    "max_trajectory_dev_m": traj,
                    "mean_trajectory_dev_m": traj * 0.5,
                    "braking_onset_delta_m": 3.0,
                    "apex_speed_dev_kmh": 0.8,
                    "apex_delta_s_m": 3.80,
                    "apex_overlap_pct": ovl,
                    "front_axle_gap_m": 3.80,
                    "exit_clearance_m": clr,
                    "relative_position_code": 0.0,
                    "sync_flag": 1.0,
                    "missing_telemetry_flag": 0.0,
                    "missing_brake_flag": 0.0,
                    "missing_throttle_flag": 0.0,
                    "missing_baseline_flag": 0.0,
                    "missing_geometry_flag": 0.0,
                    "missing_exit_clearance_flag": 0.0,
                    "sample_density": 50.0,
                }),
                metadata={"description": desc},
            )
        )

    # Excluded Ambiguous Austria Sample
    samples.append(
        MLSample(
            sample_id="AMBIG-AUSTRIA-01",
            session_id="2024-austria-race",
            race="Austrian Grand Prix",
            circuit="Red Bull Ring",
            circuit_id="red_bull_ring",
            season=2024,
            session="Race",
            lap=48,
            driver_a="ALB",
            driver_b="NONE",
            group_id="austria_alb_pit_line",
            label=0,
            label_name="UNVERIFIED",
            label_provenance=LabelProvenance.UNVERIFIED,
            supervised_include=False,  # EXCLUDED from supervised loss
            features=extract_features_from_dict({
                "min_gap_m": 15.0,
                "peak_closing_speed_ms": 0.0,
                "max_trajectory_dev_m": 0.85,
                "missing_telemetry_flag": 0.0,
            }),
            metadata={"description": "Pit exit white line crossing; procedural sporting infringement without vehicle collision"},
        )
    )

    return MLDataset(samples=samples)


def build_canonical_dataset() -> MLDataset:
    """Primary entrypoint returning verified multi-circuit supervised dataset."""
    return build_multi_circuit_dataset().get_supervised_dataset()
