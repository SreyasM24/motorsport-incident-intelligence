"""Multi-signal incident candidate detector.

CRITICAL DESIGN PRINCIPLE:
    A single telemetry channel anomaly is NEVER an incident candidate.
    This detector requires coincident, independent evidence signals across spatial,
    kinematic, and vehicle-response domains before producing an incident candidate.
    Normal racing behaviors (slipstreaming, synchronized corner entry braking,
    steady following) are explicitly filtered out.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from app.evidence.candidate import EvidenceSignal, EvidenceSignalType
from app.evidence.features import FrameFeatures


@dataclass
class DetectorConfig:
    """Configurable evidence thresholds with explicit physical justifications."""

    # 1. Spatial Proximity: F1 car length is ~5.6m, width is ~2.0m.
    # At < 10.0m cars are in immediate wheel-to-wheel proximity.
    proximity_threshold_m: float = 10.0
    critical_proximity_m: float = 5.0

    # 2. Kinematic Closing Speed:
    # 6.0 m/s (~22 km/h) relative approach rate under tight proximity.
    closing_speed_threshold_ms: float = 6.0
    high_closing_speed_ms: float = 12.0

    # 3. Deceleration Spike:
    # F1 cars brake at 4-5G into Turn 1. An asymmetric deceleration delta > 2.0G
    # indicates one car braking much harder or sudden speed scrubbing.
    decel_delta_threshold_g: float = 2.0
    severe_decel_g: float = -3.0

    # 4. Vehicle Response:
    # Asymmetric brake application (> 50% delta) under proximity indicates
    # evasive action or one car caught off-guard.
    brake_delta_threshold_pct: float = 50.0

    # 5. Signal Coincidence Requirement:
    # At least 2 independent signal types must be active to trigger a candidate.
    min_coincident_signals: int = 2

    # 6. Interaction Horizon:
    # Beyond 30.0m (~5.5 car lengths), cars cannot physically be in collision or forcing-off contact.
    # Prevents cross-circuit infield Cartesian closing artifacts between distant cars.
    max_interaction_distance_m: float = 30.0

    # 7. Lap Consistency:
    # Cars separated across different laps are not in direct racing proximity
    # unless an unlapping or blue-flag encounter occurs.
    require_same_lap: bool = True


@dataclass
class TriggeredFrame:
    """A single frame that satisfied multi-signal candidate criteria."""
    index: int
    timestamp: str
    time_offset: float
    signals: List[EvidenceSignal]
    features: FrameFeatures


class MultiSignalDetector:
    """Evaluates pairwise timeseries frames against multi-signal evidence conditions."""

    def __init__(self, config: Optional[DetectorConfig] = None):
        self.config = config or DetectorConfig()

    def evaluate_frame(self, feat: FrameFeatures) -> List[EvidenceSignal]:
        """Evaluate a single frame against independent evidence conditions."""
        signals: List[EvidenceSignal] = []

        # Enforce same-lap constraint for direct interaction candidates
        if self.config.require_same_lap and not feat.same_lap:
            return []

        # Filter out distant cars outside tactical interaction horizon (> 30m)
        if feat.gap_meters > self.config.max_interaction_distance_m:
            return []

        # Filter out verified normal racing states unless critical proximity occurs
        if feat.is_normal_slipstream and feat.gap_meters > self.config.critical_proximity_m:
            return []
        if feat.is_synchronized_braking and feat.gap_meters > self.config.critical_proximity_m:
            return []
        if feat.is_steady_following:
            return []

        # Signal A: Spatial Proximity
        if feat.gap_meters <= self.config.critical_proximity_m:
            signals.append(
                EvidenceSignal(
                    signal_type=EvidenceSignalType.SPATIAL_PROXIMITY,
                    timestamp=feat.timestamp,
                    time_offset=feat.time_offset,
                    observed_value=feat.gap_meters,
                    threshold_value=self.config.critical_proximity_m,
                    unit="m",
                    description=f"Critical proximity ({feat.gap_meters:.1f}m <= {self.config.critical_proximity_m:.1f}m)",
                )
            )
        elif feat.gap_meters <= self.config.proximity_threshold_m:
            signals.append(
                EvidenceSignal(
                    signal_type=EvidenceSignalType.SPATIAL_PROXIMITY,
                    timestamp=feat.timestamp,
                    time_offset=feat.time_offset,
                    observed_value=feat.gap_meters,
                    threshold_value=self.config.proximity_threshold_m,
                    unit="m",
                    description=f"Close wheel-to-wheel proximity ({feat.gap_meters:.1f}m <= {self.config.proximity_threshold_m:.1f}m)",
                )
            )

        # Signal B: Kinematic Closing Rate
        if feat.closing_speed_ms >= self.config.high_closing_speed_ms:
            signals.append(
                EvidenceSignal(
                    signal_type=EvidenceSignalType.KINEMATIC_CLOSING,
                    timestamp=feat.timestamp,
                    time_offset=feat.time_offset,
                    observed_value=feat.closing_speed_ms,
                    threshold_value=self.config.high_closing_speed_ms,
                    unit="m/s",
                    description=f"Severe closing rate ({feat.closing_speed_ms:.1f} m/s >= {self.config.high_closing_speed_ms:.1f} m/s)",
                )
            )
        elif feat.closing_speed_ms >= self.config.closing_speed_threshold_ms and feat.gap_meters <= self.config.proximity_threshold_m:
            signals.append(
                EvidenceSignal(
                    signal_type=EvidenceSignalType.KINEMATIC_CLOSING,
                    timestamp=feat.timestamp,
                    time_offset=feat.time_offset,
                    observed_value=feat.closing_speed_ms,
                    threshold_value=self.config.closing_speed_threshold_ms,
                    unit="m/s",
                    description=f"Rapid closing rate ({feat.closing_speed_ms:.1f} m/s >= {self.config.closing_speed_threshold_ms:.1f} m/s under proximity)",
                )
            )

        # Signal C: Asymmetric Deceleration Spike
        if feat.decel_delta_g >= self.config.decel_delta_threshold_g and (feat.accel_a_g < -1.0 or feat.accel_b_g < -1.0):
            signals.append(
                EvidenceSignal(
                    signal_type=EvidenceSignalType.DECELERATION_SPIKE,
                    timestamp=feat.timestamp,
                    time_offset=feat.time_offset,
                    observed_value=feat.decel_delta_g,
                    threshold_value=self.config.decel_delta_threshold_g,
                    unit="G",
                    description=f"Differential deceleration spike ({feat.decel_delta_g:.1f}G delta between cars)",
                )
            )

        # Signal D: Vehicle Response (Emergency / Asymmetric Braking under Proximity)
        if feat.brake_delta_pct >= self.config.brake_delta_threshold_pct and feat.gap_meters <= self.config.proximity_threshold_m:
            signals.append(
                EvidenceSignal(
                    signal_type=EvidenceSignalType.VEHICLE_RESPONSE,
                    timestamp=feat.timestamp,
                    time_offset=feat.time_offset,
                    observed_value=feat.brake_delta_pct,
                    threshold_value=self.config.brake_delta_threshold_pct,
                    unit="%",
                    description=f"Asymmetric braking response ({feat.brake_delta_pct:.0f}% brake delta under proximity)",
                )
            )

        return signals

    def detect_candidate_frames(self, features: List[FrameFeatures]) -> List[TriggeredFrame]:
        """Scan feature timeseries and collect frames meeting multi-signal criteria."""
        triggered: List[TriggeredFrame] = []

        for feat in features:
            signals = self.evaluate_frame(feat)
            # Count distinct signal types
            unique_types = {s.signal_type for s in signals}

            if len(unique_types) >= self.config.min_coincident_signals:
                triggered.append(
                    TriggeredFrame(
                        index=feat.index,
                        timestamp=feat.timestamp,
                        time_offset=feat.time_offset,
                        signals=signals,
                        features=feat,
                    )
                )

        return triggered
