"""Canonical Machine Learning Feature Registry and Governance (Prompt 26).

CRITICAL SCIENTIFIC & JURISPRUDENTIAL GUARDRAILS:
    1. STRICT EXCLUSION OF ADJUDICATIVE ATTRIBUTES:
       Features quantifying steward penalties, guilt, fault, driver identity, team identity,
       championship standings, or post-race outcomes are FORBIDDEN.
    2. EPISTEMIC GROUNDING:
       Every feature is explicitly classified by epistemic origin (OBSERVED, DERIVED, MODEL_DERIVED).
    3. TEMPORAL LEAKAGE CONTROLS:
       Every feature must be strictly available at the moment of incident investigation.
    4. NO IMPROBABLE HEURISTICS:
       A feature is never permitted merely because it improves validation accuracy on small cohorts.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


class FeatureGovernanceStatus(str, Enum):
    """Regulatory governance classification of features."""
    ALLOWED = "ALLOWED"          # Strictly verified physical, kinematic, or quality signal
    CONDITIONAL = "CONDITIONAL"  # Allowed only under verified data quality or telemetry coverage
    FORBIDDEN = "FORBIDDEN"      # Strictly prohibited from entering training or inference matrices


class FeatureEpistemicType(str, Enum):
    """Epistemic nature of the feature signal."""
    OBSERVED = "OBSERVED"              # Direct sensor measurement (CAN-bus, GPS, sync flag)
    DERIVED = "DERIVED"                # Mathematically computed from sensor data (e.g. Euclidean gap, closing speed)
    MODEL_DERIVED = "MODEL_DERIVED"    # Output of upstream analytical model (e.g. baseline deviation, apex overlap)
    DOCUMENTARY = "DOCUMENTARY"        # Statutory / official steward document text


class FeatureAvailability(str, Enum):
    """Temporal and physical availability requirement."""
    ALWAYS_AVAILABLE = "ALWAYS_AVAILABLE"
    TELEMETRY_DEPENDENT = "TELEMETRY_DEPENDENT"
    REFERENCE_LAP_DEPENDENT = "REFERENCE_LAP_DEPENDENT"
    GEOMETRY_DEPENDENT = "GEOMETRY_DEPENDENT"


class FeatureGovernanceMetadata(BaseModel):
    """Canonical governance specification for an individual feature."""
    feature_name: str
    semantic_definition: str
    source: str
    units: str
    epistemic_type: FeatureEpistemicType
    availability: FeatureAvailability
    preprocessing: str
    leakage_risk: str
    governance_status: FeatureGovernanceStatus
    allowed_for_training: bool
    allowed_for_inference: bool
    notes: Optional[str] = None


# Canonical Registry for All Active and Potential Features
FEATURE_REGISTRY: Dict[str, FeatureGovernanceMetadata] = {
    # -------------------------------------------------------------------------
    # 1. KINEMATICS (ALLOWED)
    # -------------------------------------------------------------------------
    "min_gap_m": FeatureGovernanceMetadata(
        feature_name="min_gap_m",
        semantic_definition="Minimum measured Euclidean 2D separation distance between vehicle centroids",
        source="FastF1 25Hz Cartesian Coordinates",
        units="meters",
        epistemic_type=FeatureEpistemicType.DERIVED,
        availability=FeatureAvailability.TELEMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 15.0m for non-interacting states",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "peak_closing_speed_ms": FeatureGovernanceMetadata(
        feature_name="peak_closing_speed_ms",
        semantic_definition="Maximum rate of proximity closure along the line of sight across interaction window",
        source="Central Euclidean difference on 25Hz Cartesian trajectories",
        units="m/s",
        epistemic_type=FeatureEpistemicType.DERIVED,
        availability=FeatureAvailability.TELEMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0 m/s",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "mean_closing_speed_ms": FeatureGovernanceMetadata(
        feature_name="mean_closing_speed_ms",
        semantic_definition="Mean rate of proximity closure across approach phase leading to closest proximity",
        source="Central Euclidean difference on 25Hz Cartesian trajectories",
        units="m/s",
        epistemic_type=FeatureEpistemicType.DERIVED,
        availability=FeatureAvailability.TELEMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0 m/s",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "speed_delta_kmh": FeatureGovernanceMetadata(
        feature_name="speed_delta_kmh",
        semantic_definition="Absolute speed difference between Car A and Car B at the point of closest proximity",
        source="ECU Wheel-Speed CAN-bus telemetry",
        units="km/h",
        epistemic_type=FeatureEpistemicType.DERIVED,
        availability=FeatureAvailability.TELEMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0 km/h",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "brake_delta_pct": FeatureGovernanceMetadata(
        feature_name="brake_delta_pct",
        semantic_definition="Absolute difference in brake pedal application percentages at closest proximity",
        source="ECU Hydraulic Brake Pressure CAN-bus",
        units="percentage",
        epistemic_type=FeatureEpistemicType.DERIVED,
        availability=FeatureAvailability.TELEMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0 paired with missing_brake_flag indicator",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "throttle_delta_pct": FeatureGovernanceMetadata(
        feature_name="throttle_delta_pct",
        semantic_definition="Absolute difference in throttle pedal application percentages at closest proximity",
        source="ECU Fly-by-Wire Throttle Position CAN-bus",
        units="percentage",
        epistemic_type=FeatureEpistemicType.DERIVED,
        availability=FeatureAvailability.TELEMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0 paired with missing_throttle_flag indicator",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "accel_delta_g": FeatureGovernanceMetadata(
        feature_name="accel_delta_g",
        semantic_definition="Longitudinal acceleration differential between vehicles at closest proximity",
        source="IMU / Differentiated Wheel Speed",
        units="g",
        epistemic_type=FeatureEpistemicType.DERIVED,
        availability=FeatureAvailability.TELEMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0 g",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),

    # -------------------------------------------------------------------------
    # 2. REFERENCE-LAP BASELINE DEVIATIONS (ALLOWED)
    # -------------------------------------------------------------------------
    "max_trajectory_dev_m": FeatureGovernanceMetadata(
        feature_name="max_trajectory_dev_m",
        semantic_definition="Maximum orthogonal lateral trajectory deviation from clean reference-lap racing line",
        source="Reference-Lap Baseline Comparison Engine",
        units="meters",
        epistemic_type=FeatureEpistemicType.MODEL_DERIVED,
        availability=FeatureAvailability.REFERENCE_LAP_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0m paired with missing_baseline_flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "mean_trajectory_dev_m": FeatureGovernanceMetadata(
        feature_name="mean_trajectory_dev_m",
        semantic_definition="Mean lateral trajectory deviation across interaction approach and apex phases",
        source="Reference-Lap Baseline Comparison Engine",
        units="meters",
        epistemic_type=FeatureEpistemicType.MODEL_DERIVED,
        availability=FeatureAvailability.REFERENCE_LAP_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0m paired with missing_baseline_flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "braking_onset_delta_m": FeatureGovernanceMetadata(
        feature_name="braking_onset_delta_m",
        semantic_definition="Spatial longitudinal displacement of initial braking onset point relative to reference baseline",
        source="Reference-Lap Baseline Comparison Engine",
        units="meters",
        epistemic_type=FeatureEpistemicType.MODEL_DERIVED,
        availability=FeatureAvailability.REFERENCE_LAP_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0m paired with missing_baseline_flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "apex_speed_dev_kmh": FeatureGovernanceMetadata(
        feature_name="apex_speed_dev_kmh",
        semantic_definition="Corner apex speed deficit or surplus compared to median reference-lap apex speed",
        source="Reference-Lap Baseline Comparison Engine",
        units="km/h",
        epistemic_type=FeatureEpistemicType.MODEL_DERIVED,
        availability=FeatureAvailability.REFERENCE_LAP_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0 km/h paired with missing_baseline_flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),

    # -------------------------------------------------------------------------
    # 3. CORNERING OVERTAKE GEOMETRY (ALLOWED)
    # -------------------------------------------------------------------------
    "apex_delta_s_m": FeatureGovernanceMetadata(
        feature_name="apex_delta_s_m",
        semantic_definition="Longitudinal distance between vehicles measured along the track centerline at corner apex",
        source="Overtake Geometry Service (Frenet coordinate frame projection)",
        units="meters",
        epistemic_type=FeatureEpistemicType.MODEL_DERIVED,
        availability=FeatureAvailability.GEOMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 10.0m paired with missing_geometry_flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "apex_overlap_pct": FeatureGovernanceMetadata(
        feature_name="apex_overlap_pct",
        semantic_definition="Percentage of vehicle length overlapped longitudinally at the corner apex (FIA Driving Standards reference)",
        source="Overtake Geometry Service (5.63m standard chassis bounding box projection)",
        units="percentage",
        epistemic_type=FeatureEpistemicType.MODEL_DERIVED,
        availability=FeatureAvailability.GEOMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 0.0% paired with missing_geometry_flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "front_axle_gap_m": FeatureGovernanceMetadata(
        feature_name="front_axle_gap_m",
        semantic_definition="Longitudinal displacement between front axles at corner entry/apex",
        source="Overtake Geometry Service",
        units="meters",
        epistemic_type=FeatureEpistemicType.MODEL_DERIVED,
        availability=FeatureAvailability.GEOMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 10.0m paired with missing_geometry_flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "exit_clearance_m": FeatureGovernanceMetadata(
        feature_name="exit_clearance_m",
        semantic_definition="Measured lateral distance between the outside car and track limits edge at corner exit",
        source="Overtake Geometry Service (Exit track limit spatial projection)",
        units="meters",
        epistemic_type=FeatureEpistemicType.MODEL_DERIVED,
        availability=FeatureAvailability.GEOMETRY_DEPENDENT,
        preprocessing="StandardScaler with sentinel 2.0m (one car width) paired with missing_exit_clearance_flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "relative_position_code": FeatureGovernanceMetadata(
        feature_name="relative_position_code",
        semantic_definition="Categorical longitudinal ordering code: +1.0 (ahead), 0.0 (alongside), -1.0 (behind)",
        source="Overtake Geometry Service",
        units="discrete_code",
        epistemic_type=FeatureEpistemicType.MODEL_DERIVED,
        availability=FeatureAvailability.GEOMETRY_DEPENDENT,
        preprocessing="Passthrough ordinal code",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),

    # -------------------------------------------------------------------------
    # 4. DATA QUALITY & EXPLICIT MISSINGNESS FLAGS (ALLOWED)
    # -------------------------------------------------------------------------
    "sync_flag": FeatureGovernanceMetadata(
        feature_name="sync_flag",
        semantic_definition="Temporal synchronization validity indicator (1.0 = valid, 0.0 = desynchronized)",
        source="Telemetry Ingestion / Clock Synchronization",
        units="binary_flag",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="Passthrough flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "missing_telemetry_flag": FeatureGovernanceMetadata(
        feature_name="missing_telemetry_flag",
        semantic_definition="Indicator flag set to 1.0 when telemetry stream is absent or unavailable",
        source="Ingestion Pipeline Validation",
        units="binary_flag",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="Passthrough flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "missing_brake_flag": FeatureGovernanceMetadata(
        feature_name="missing_brake_flag",
        semantic_definition="Indicator flag set to 1.0 when brake sensor channel is unobserved",
        source="ECU Stream Health Validator",
        units="binary_flag",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="Passthrough flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "missing_throttle_flag": FeatureGovernanceMetadata(
        feature_name="missing_throttle_flag",
        semantic_definition="Indicator flag set to 1.0 when throttle sensor channel is unobserved",
        source="ECU Stream Health Validator",
        units="binary_flag",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="Passthrough flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "missing_baseline_flag": FeatureGovernanceMetadata(
        feature_name="missing_baseline_flag",
        semantic_definition="Indicator flag set to 1.0 when reference-lap baseline telemetry is unavailable",
        source="Reference Lap Validator",
        units="binary_flag",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="Passthrough flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "missing_geometry_flag": FeatureGovernanceMetadata(
        feature_name="missing_geometry_flag",
        semantic_definition="Indicator flag set to 1.0 when track corner geometry model is unavailable",
        source="Track Map Geometry Validator",
        units="binary_flag",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="Passthrough flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "missing_exit_clearance_flag": FeatureGovernanceMetadata(
        feature_name="missing_exit_clearance_flag",
        semantic_definition="Indicator flag set to 1.0 when corner exit spatial clearance channel is unobserved",
        source="Geometry Validator",
        units="binary_flag",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="Passthrough flag",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),
    "sample_density": FeatureGovernanceMetadata(
        feature_name="sample_density",
        semantic_definition="Total valid telemetry frames recorded within the interaction analysis window",
        source="Telemetry Ingestion Grid",
        units="frame_count",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="StandardScaler",
        leakage_risk="NONE",
        governance_status=FeatureGovernanceStatus.ALLOWED,
        allowed_for_training=True,
        allowed_for_inference=True,
    ),

    # -------------------------------------------------------------------------
    # 5. FORBIDDEN ADJUDICATIVE & IDENTITY ATTRIBUTES (STRICTLY PROHIBITED)
    # -------------------------------------------------------------------------
    "fia_penalty_outcome": FeatureGovernanceMetadata(
        feature_name="fia_penalty_outcome",
        semantic_definition="Steward decision outcome or sporting penalty applied to a driver",
        source="FIA Official Document",
        units="adjudicative_string",
        epistemic_type=FeatureEpistemicType.DOCUMENTARY,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="PROHIBITED",
        leakage_risk="FATAL_ADJUDICATIVE_LEAKAGE",
        governance_status=FeatureGovernanceStatus.FORBIDDEN,
        allowed_for_training=False,
        allowed_for_inference=False,
        notes="Violates non-adjudication doctrine; represents judicial decision, not physical telemetry.",
    ),
    "steward_verdict": FeatureGovernanceMetadata(
        feature_name="steward_verdict",
        semantic_definition="Documented verdict or fault allocation by FIA stewards",
        source="FIA Official Document",
        units="verdict_string",
        epistemic_type=FeatureEpistemicType.DOCUMENTARY,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="PROHIBITED",
        leakage_risk="FATAL_ADJUDICATIVE_LEAKAGE",
        governance_status=FeatureGovernanceStatus.FORBIDDEN,
        allowed_for_training=False,
        allowed_for_inference=False,
        notes="Post-incident legal adjudication; cannot serve as model input.",
    ),
    "driver_identity": FeatureGovernanceMetadata(
        feature_name="driver_identity",
        semantic_definition="Driver name, acronym, code, or permanent driver number",
        source="Entry List",
        units="identifier",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="PROHIBITED",
        leakage_risk="FATAL_BIAS_LEAKAGE",
        governance_status=FeatureGovernanceStatus.FORBIDDEN,
        allowed_for_training=False,
        allowed_for_inference=False,
        notes="Models must be driver-invariant. Identity induces reputational bias and overfitting.",
    ),
    "team_identity": FeatureGovernanceMetadata(
        feature_name="team_identity",
        semantic_definition="Constructor or team name",
        source="Entry List",
        units="identifier",
        epistemic_type=FeatureEpistemicType.OBSERVED,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="PROHIBITED",
        leakage_risk="FATAL_BIAS_LEAKAGE",
        governance_status=FeatureGovernanceStatus.FORBIDDEN,
        allowed_for_training=False,
        allowed_for_inference=False,
        notes="Models must be team-invariant.",
    ),
    "championship_standing": FeatureGovernanceMetadata(
        feature_name="championship_standing",
        semantic_definition="Current driver or constructor world championship points or ranking",
        source="Championship Standings Table",
        units="points / rank",
        epistemic_type=FeatureEpistemicType.DOCUMENTARY,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="PROHIBITED",
        leakage_risk="FATAL_BIAS_LEAKAGE",
        governance_status=FeatureGovernanceStatus.FORBIDDEN,
        allowed_for_training=False,
        allowed_for_inference=False,
        notes="Irrelevant to physical collision mechanics; induces championship-level bias.",
    ),
    "driver_nationality": FeatureGovernanceMetadata(
        feature_name="driver_nationality",
        semantic_definition="Driver country of origin or license authority",
        source="FIA Entry List",
        units="country_code",
        epistemic_type=FeatureEpistemicType.DOCUMENTARY,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="PROHIBITED",
        leakage_risk="FATAL_BIAS_LEAKAGE",
        governance_status=FeatureGovernanceStatus.FORBIDDEN,
        allowed_for_training=False,
        allowed_for_inference=False,
        notes="Discriminatory demographic attribute; strictly prohibited.",
    ),
    "driver_reputation": FeatureGovernanceMetadata(
        feature_name="driver_reputation",
        semantic_definition="Historical penalty point total or steward investigation frequency",
        source="Steward Database",
        units="points",
        epistemic_type=FeatureEpistemicType.DOCUMENTARY,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="PROHIBITED",
        leakage_risk="FATAL_BIAS_LEAKAGE",
        governance_status=FeatureGovernanceStatus.FORBIDDEN,
        allowed_for_training=False,
        allowed_for_inference=False,
        notes="Induces prior-history bias in physical anomaly evaluation.",
    ),
    "historical_penalty": FeatureGovernanceMetadata(
        feature_name="historical_penalty",
        semantic_definition="Prior penalty records in the same race or preceding events",
        source="Steward Database",
        units="penalty_code",
        epistemic_type=FeatureEpistemicType.DOCUMENTARY,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="PROHIBITED",
        leakage_risk="FATAL_ADJUDICATIVE_LEAKAGE",
        governance_status=FeatureGovernanceStatus.FORBIDDEN,
        allowed_for_training=False,
        allowed_for_inference=False,
        notes="Steward penalties are not physical features.",
    ),
    "post_incident_outcome": FeatureGovernanceMetadata(
        feature_name="post_incident_outcome",
        semantic_definition="Post-incident race result, retirement status, or steward hearing transcript",
        source="Post-Race Timing / Stewards",
        units="result_code",
        epistemic_type=FeatureEpistemicType.DOCUMENTARY,
        availability=FeatureAvailability.ALWAYS_AVAILABLE,
        preprocessing="PROHIBITED",
        leakage_risk="FATAL_TEMPORAL_LEAKAGE",
        governance_status=FeatureGovernanceStatus.FORBIDDEN,
        allowed_for_training=False,
        allowed_for_inference=False,
        notes="Information unavailable at the moment the incident required review.",
    ),
}

# Explicit Sets for High-Performance Membership Auditing
ALLOWED_FEATURE_NAMES: Set[str] = {
    name for name, meta in FEATURE_REGISTRY.items()
    if meta.governance_status == FeatureGovernanceStatus.ALLOWED
}

FORBIDDEN_FEATURE_NAMES: Set[str] = {
    name for name, meta in FEATURE_REGISTRY.items()
    if meta.governance_status == FeatureGovernanceStatus.FORBIDDEN
}


# ==============================================================================
# AUDIT & GOVERNANCE UTILITIES
# ==============================================================================

def get_feature_registry() -> Dict[str, FeatureGovernanceMetadata]:
    """Retrieve full canonical feature governance registry."""
    return dict(FEATURE_REGISTRY)


def is_feature_allowed(name: str) -> bool:
    """Check whether a feature name is certified as ALLOWED for model ingestion."""
    meta = FEATURE_REGISTRY.get(name)
    if not meta:
        return False
    return meta.governance_status == FeatureGovernanceStatus.ALLOWED


def get_forbidden_feature_names() -> List[str]:
    """Retrieve all certified FORBIDDEN feature names."""
    return sorted(list(FORBIDDEN_FEATURE_NAMES))


def validate_feature_schema(schema: List[str]) -> Tuple[bool, List[str]]:
    """Assert that a feature schema contains ZERO forbidden or unknown attributes."""
    violations: List[str] = []
    for feat in schema:
        if feat in FORBIDDEN_FEATURE_NAMES:
            violations.append(f"FORBIDDEN_FEATURE_DETECTED: '{feat}' is strictly prohibited.")
        elif feat not in ALLOWED_FEATURE_NAMES:
            violations.append(f"UNREGISTERED_FEATURE_DETECTED: '{feat}' is not in the canonical registry.")
    return len(violations) == 0, violations


def audit_dictionary_for_forbidden_leakage(data_dict: Dict[str, Any]) -> List[str]:
    """Check a dictionary of candidate/sample data for forbidden adjudicative or identity fields."""
    leaked: List[str] = []
    # Direct match on forbidden feature keys
    for k in data_dict.keys():
        k_lower = k.lower()
        if k_lower in FORBIDDEN_FEATURE_NAMES:
            leaked.append(k)
        # Catch common variations of forbidden attributes
        elif any(f in k_lower for f in [
            "penalty", "verdict", "guilt", "blame", "reputation",
            "standing", "nationality", "popularity", "steward_finding"
        ]):
            leaked.append(k)
    return leaked
