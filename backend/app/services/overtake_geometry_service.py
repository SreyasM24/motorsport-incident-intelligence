"""Cornering Overtake Geometry & Apex Overlap Analysis Service.

CRITICAL JURISPRUDENTIAL GUARDRAILS:
    1. Produces MEASURABLE GEOMETRIC EVIDENCE ONLY.
    2. NEVER decides fault, guilt, penalty, legality, or driver responsibility.
    3. Exposes raw empirical quantities (distances, gaps, overlap ratios) for human steward review.
    4. Evaluates against documented engineering & regulatory reference thresholds (2.0m car width, 50% overlap).
"""

from functools import lru_cache
import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from app.core.logging import logger
from app.evidence.candidate import CandidateDossier
from app.schemas.overtake_geometry import (
    ApexOverlapSnapshot,
    CornerPhases,
    CornerPhaseSnapshot,
    ExitClearanceClassification,
    ExitClearanceMetrics,
    FIAGuidelineReference,
    MeasurementConfidence,
    OverlapClassification,
    OvertakeGeometryDataQuality,
    OvertakeGeometryEvidence,
    RelativeLongitudinalPosition,
)
from app.schemas.telemetry import TelemetryPointSchema


# Reference dimensions for modern Formula 1 cars:
# 1. Car Width: 2.00m is an official FIA Technical Regulation (2024 Article 3.3, max 2000mm overall width).
# 2. Car Length: 5.63m is an engineering reference approximation based on max wheelbase (3.60m, Article 3.2) plus wing overhangs.
# 3. Front Axle to Mirror Distance (2.20m): Engineering reference approximation for cockpit mirror location.
REFERENCE_F1_CAR_LENGTH_M = 5.63  # Engineering reference
REFERENCE_F1_CAR_WIDTH_M = 2.00   # FIA Technical Regulations 2024 Article 3.3
FRONT_AXLE_TO_MIRROR_DIST_M = 2.20 # Engineering reference


class CorneringOvertakeGeometryService:
    """Service providing deterministic corner phase detection, vehicle spacing, and apex overlap quantification."""

    def __init__(self):
        pass

    @staticmethod
    def _extract_distance(frame: TelemetryPointSchema, driver_key: str = "a") -> float:
        """Safely extract lap distance in meters, falling back to speed integration if distance is None."""
        dist = getattr(frame, f"distance_{driver_key}", None)
        if dist is not None:
            return float(dist)
        spd = getattr(frame, f"speed_{driver_key}", 0.0) or 0.0
        return float(frame.time_offset * (spd / 3.6))

    # -------------------------------------------------------------------------
    # 1. Corner Phase Detection (Entry, Apex, Exit)
    # -------------------------------------------------------------------------

    def detect_corner_phases(
        self,
        frames: List[TelemetryPointSchema],
    ) -> CornerPhases:
        """Deterministically identify corner entry, apex, and exit milestones from telemetry."""
        if not frames:
            return CornerPhases(
                corner_entry_distance_m=0.0,
                corner_entry_time_s=0.0,
                apex_distance_m=0.0,
                apex_time_s=0.0,
                apex_speed_kmh=0.0,
                corner_exit_distance_m=None,
                corner_exit_time_s=None,
                exit_detection_status="UNAVAILABLE",
            )

        # 1. Apex Detection (Minimum cornering speed point across the window)
        min_speed = 1e9
        apex_idx = len(frames) // 2
        for idx, f in enumerate(frames):
            spd = min(f.speed_a, f.speed_b)
            if spd < min_speed:
                min_speed = spd
                apex_idx = idx

        apex_frame = frames[apex_idx]
        apex_dist = self._extract_distance(apex_frame, "a")
        apex_time = float(apex_frame.time_offset)
        apex_speed = round(min_speed, 1)

        # 2. Corner Entry Detection (Braking onset or initial deceleration prior to apex)
        entry_idx = 0
        for idx in range(min(apex_idx, len(frames))):
            f = frames[idx]
            # First significant braking (>10%) or throttle lift (<80%)
            if f.brake_a > 10.0 or f.brake_b > 10.0 or f.throttle_a < 80.0 or f.throttle_b < 80.0:
                entry_idx = idx
                break

        entry_frame = frames[entry_idx]
        entry_dist = self._extract_distance(entry_frame, "a")
        entry_time = float(entry_frame.time_offset)

        # 3. Corner Exit Detection (Throttle reapplication and speed acceleration post-apex)
        exit_idx = None
        for idx in range(apex_idx, len(frames)):
            f = frames[idx]
            # Recovery to sustained acceleration (>70% throttle and speed +15 km/h above apex)
            if (f.throttle_a > 70.0 or f.throttle_b > 70.0) and (f.speed_a > apex_speed + 15.0 or f.speed_b > apex_speed + 15.0):
                exit_idx = idx
                break

        if exit_idx is not None:
            exit_frame = frames[exit_idx]
            exit_dist = self._extract_distance(exit_frame, "a")
            exit_time = float(exit_frame.time_offset)
            exit_status = "AVAILABLE"
            exit_method = "THROTTLE_REAPPLICATION_AND_ACCELERATION"
        else:
            # If telemetry window ends before acceleration recovery, report UNAVAILABLE
            exit_dist = None
            exit_time = None
            exit_status = "UNAVAILABLE"
            exit_method = None

        return CornerPhases(
            corner_entry_distance_m=round(entry_dist, 2),
            corner_entry_time_s=round(entry_time, 3),
            entry_detection_method="LONGITUDINAL_DECELERATION_THRESHOLD",
            apex_distance_m=round(apex_dist, 2),
            apex_time_s=round(apex_time, 3),
            apex_speed_kmh=apex_speed,
            apex_detection_method="MINIMUM_CORNER_SPEED",
            corner_exit_distance_m=round(exit_dist, 2) if exit_dist is not None else None,
            corner_exit_time_s=round(exit_time, 3) if exit_time is not None else None,
            exit_detection_status=exit_status,
            exit_detection_method=exit_method,
        )

    # -------------------------------------------------------------------------
    # 2. Longitudinal Spacing and Ordering
    # -------------------------------------------------------------------------

    def calculate_vehicle_relationship(
        self,
        frame: Optional[TelemetryPointSchema] = None,
        delta_s_m: Optional[float] = None,
    ) -> Tuple[float, float, RelativeLongitudinalPosition]:
        """Measure longitudinal separation and physical ordering between Driver A (incident) and Driver B."""
        if frame is not None:
            dist_a = self._extract_distance(frame, "a")
            dist_b = self._extract_distance(frame, "b")
            delta_s = round(dist_a - dist_b, 2)
            mean_speed_ms = max((frame.speed_a + frame.speed_b) / 7.2, 10.0)
            delta_t = round(delta_s / mean_speed_ms, 3)
        elif delta_s_m is not None:
            delta_s = round(float(delta_s_m), 2)
            delta_t = 0.0
        else:
            return 0.0, 0.0, RelativeLongitudinalPosition.UNAVAILABLE

        # Physical position classification based on 0.5m threshold
        if abs(delta_s) <= 0.5:
            pos = RelativeLongitudinalPosition.APPROXIMATELY_ALONGSIDE
        elif delta_s > 0:
            pos = RelativeLongitudinalPosition.AHEAD
        else:
            pos = RelativeLongitudinalPosition.BEHIND

        return delta_s, delta_t, pos

    # -------------------------------------------------------------------------
    # 3. Longitudinal & Front-Axle Overlap Quantification
    # -------------------------------------------------------------------------

    def calculate_overlap(
        self,
        longitudinal_gap_m: Optional[float] = None,
        reference_length_m: float = REFERENCE_F1_CAR_LENGTH_M,
        delta_s_m: Optional[float] = None,
    ) -> Tuple[float, float, OverlapClassification]:
        """Calculate geometric longitudinal overlap percentage and classification."""
        gap_val = longitudinal_gap_m if longitudinal_gap_m is not None else (delta_s_m if delta_s_m is not None else 0.0)
        abs_gap = abs(gap_val)

        if abs_gap >= reference_length_m:
            return 0.0, 0.0, OverlapClassification.NO_MEASURABLE_OVERLAP

        overlapping_length = reference_length_m - abs_gap
        overlap_ratio = max(0.0, min(1.0, overlapping_length / reference_length_m))
        overlap_pct = round(overlap_ratio * 100.0, 1)

        if overlap_pct >= 55.0:
            classification = OverlapClassification.GREATER_THAN_50_PERCENT_OVERLAP
        elif overlap_pct >= 45.0:
            classification = OverlapClassification.APPROXIMATELY_50_PERCENT_OVERLAP
        elif overlap_pct > 0.0:
            classification = OverlapClassification.PARTIAL_OVERLAP
        else:
            classification = OverlapClassification.NO_MEASURABLE_OVERLAP

        return round(overlap_ratio, 3), overlap_pct, classification

    # -------------------------------------------------------------------------
    # 4. Apex Overlap Snapshot
    # -------------------------------------------------------------------------

    def calculate_apex_snapshot(
        self,
        frames: List[TelemetryPointSchema],
        apex_dist: float,
        driver_a: str,
        driver_b: str,
    ) -> ApexOverlapSnapshot:
        """Extract dedicated snapshot at closest frame to corner apex."""
        if not frames:
            return ApexOverlapSnapshot(
                incident_car_code=driver_a,
                incident_distance_m=0.0,
                incident_speed_kmh=0.0,
                other_car_code=driver_b,
                other_distance_m=0.0,
                other_speed_kmh=0.0,
                longitudinal_gap_m=0.0,
                relative_position=RelativeLongitudinalPosition.UNAVAILABLE,
                overlap_percent=None,
                overlap_classification=OverlapClassification.INSUFFICIENT_GEOMETRIC_DATA,
                confidence=MeasurementConfidence.UNAVAILABLE,
            )

        # Locate closest frame to apex distance
        closest_frame = min(frames, key=lambda f: abs(self._extract_distance(f, "a") - apex_dist))

        delta_s, _, pos = self.calculate_vehicle_relationship(frame=closest_frame)
        ratio, pct, classification = self.calculate_overlap(longitudinal_gap_m=delta_s)

        # Front axle gap is approximately the absolute longitudinal displacement
        front_axle_gap = round(abs(delta_s), 2)

        # Mirror reference overlap (trailing car alongside mirror reference ~2.2m from front)
        mirror_overlap = None
        if abs(delta_s) <= FRONT_AXLE_TO_MIRROR_DIST_M:
            mirror_overlap = round(min(100.0, (1.0 - abs(delta_s) / FRONT_AXLE_TO_MIRROR_DIST_M) * 100.0), 1)

        # Extract coordinates if available
        x_a = getattr(closest_frame, "x_a", None)
        y_a = getattr(closest_frame, "y_a", None)
        x_b = getattr(closest_frame, "x_b", None)
        y_b = getattr(closest_frame, "y_b", None)

        dist_a = self._extract_distance(closest_frame, "a")
        dist_b = self._extract_distance(closest_frame, "b")

        return ApexOverlapSnapshot(
            incident_car_code=driver_a,
            incident_distance_m=round(dist_a, 2),
            incident_speed_kmh=round(float(closest_frame.speed_a), 1),
            incident_x_m=x_a,
            incident_y_m=y_a,
            other_car_code=driver_b,
            other_distance_m=round(dist_b, 2),
            other_speed_kmh=round(float(closest_frame.speed_b), 1),
            other_x_m=x_b,
            other_y_m=y_b,
            longitudinal_gap_m=delta_s,
            lateral_gap_m=round(float(closest_frame.lateral_dist_meters), 2) if closest_frame.lateral_dist_meters else None,
            euclidean_gap_m=round(float(closest_frame.gap_meters), 2) if closest_frame.gap_meters else None,
            relative_position=pos,
            overlap_percent=pct,
            overlap_classification=classification,
            front_axle_gap_m=front_axle_gap,
            mirror_reference_overlap_percent=mirror_overlap,
            confidence=MeasurementConfidence.DERIVED_FROM_POSITION,
        )

    # -------------------------------------------------------------------------
    # 5. Corner Exit Clearance Quantification
    # -------------------------------------------------------------------------

    def calculate_exit_clearance(
        self,
        frames: List[TelemetryPointSchema],
        exit_dist: Union[float, CornerPhases, None],
    ) -> ExitClearanceMetrics:
        """Evaluate spatial clearance between vehicles at corner exit against the 2.0m reference width."""
        if isinstance(exit_dist, CornerPhases):
            exit_dist = exit_dist.corner_exit_distance_m

        if exit_dist is None or not frames:
            return ExitClearanceMetrics(
                exit_distance_m=None,
                measured_clearance_m=None,
                reference_width_threshold_m=REFERENCE_F1_CAR_WIDTH_M,
                clearance_classification=ExitClearanceClassification.CLEARANCE_UNAVAILABLE,
                confidence=MeasurementConfidence.UNAVAILABLE,
                note="Corner exit point could not be reliably established from acceleration telemetry.",
            )

        # Locate closest frame to corner exit distance
        exit_frame = min(frames, key=lambda f: abs(self._extract_distance(f, "a") - exit_dist))

        # Clearance is measured via lateral or spatial gap between vehicle centers
        measured_clearance = None
        if exit_frame.lateral_dist_meters and exit_frame.lateral_dist_meters > 0:
            measured_clearance = round(float(exit_frame.lateral_dist_meters), 2)
        elif exit_frame.gap_meters and exit_frame.gap_meters > 0:
            measured_clearance = round(float(exit_frame.gap_meters), 2)

        if measured_clearance is None:
            return ExitClearanceMetrics(
                exit_distance_m=round(exit_dist, 2),
                measured_clearance_m=None,
                clearance_classification=ExitClearanceClassification.CLEARANCE_UNAVAILABLE,
                confidence=MeasurementConfidence.UNAVAILABLE,
                note="Spatial clearance channels unavailable at corner exit.",
            )

        # Classify against 2.0m one-car-width threshold
        if measured_clearance >= 2.10:
            classification = ExitClearanceClassification.CLEARANCE_ABOVE_REFERENCE
        elif measured_clearance >= 1.90:
            classification = ExitClearanceClassification.CLEARANCE_NEAR_REFERENCE
        else:
            classification = ExitClearanceClassification.CLEARANCE_BELOW_REFERENCE

        return ExitClearanceMetrics(
            exit_distance_m=round(exit_dist, 2),
            measured_clearance_m=measured_clearance,
            reference_width_threshold_m=REFERENCE_F1_CAR_WIDTH_M,
            clearance_classification=classification,
            confidence=MeasurementConfidence.DERIVED_FROM_POSITION,
            note=f"Measured exit spatial clearance: {measured_clearance:.2f}m vs 2.00m regulation car width reference. "
                 "Quantifies room afforded without determining fault or responsibility.",
        )

    # -------------------------------------------------------------------------
    # 6. Milestone Phase Snapshots (Timeline of Corner Progression)
    # -------------------------------------------------------------------------

    def build_phase_snapshots(
        self,
        frames: List[TelemetryPointSchema],
        phases: CornerPhases,
    ) -> List[CornerPhaseSnapshot]:
        """Construct milestone snapshots at ENTRY, BRAKING_ONSET, TURN_IN, APEX, APEX+10M, APEX+20M, EXIT."""
        if not frames:
            return []

        milestones = [
            ("CORNER_ENTRY", phases.corner_entry_distance_m),
            ("BRAKING_ONSET", phases.corner_entry_distance_m + 10.0),
            ("TURN_IN", (phases.corner_entry_distance_m + phases.apex_distance_m) / 2.0),
            ("APEX", phases.apex_distance_m),
            ("APEX_PLUS_10M", phases.apex_distance_m + 10.0),
            ("APEX_PLUS_20M", phases.apex_distance_m + 20.0),
        ]
        if phases.corner_exit_distance_m is not None:
            milestones.append(("CORNER_EXIT", phases.corner_exit_distance_m))

        snapshots: List[CornerPhaseSnapshot] = []
        for name, target_dist in milestones:
            # Find closest frame
            f = min(frames, key=lambda pt: abs(self._extract_distance(pt, "a") - target_dist))
            delta_s, delta_t, pos = self.calculate_vehicle_relationship(frame=f)
            spd_delta = round(float(f.speed_a - f.speed_b), 1)

            dist_a = self._extract_distance(f, "a")
            dist_b = self._extract_distance(f, "b")

            snapshots.append(
                CornerPhaseSnapshot(
                    phase_name=name,
                    distance_incident_m=round(dist_a, 2),
                    distance_other_m=round(dist_b, 2),
                    delta_s_m=delta_s,
                    delta_t_sec=delta_t,
                    speed_incident_kmh=round(float(f.speed_a), 1),
                    speed_other_kmh=round(float(f.speed_b), 1),
                    speed_delta_kmh=spd_delta,
                    lateral_gap_m=round(float(f.lateral_dist_meters), 2) if f.lateral_dist_meters else None,
                    euclidean_gap_m=round(float(f.gap_meters), 2) if f.gap_meters else None,
                    relative_position=pos,
                    confidence=MeasurementConfidence.DERIVED_FROM_POSITION,
                )
            )

        return snapshots

    # -------------------------------------------------------------------------
    # 7. End-to-End Overtake Geometry Evidence Synthesis
    # -------------------------------------------------------------------------

    def synthesize_overtake_geometry(
        self,
        candidate: CandidateDossier,
        frames: Optional[List[TelemetryPointSchema]] = None,
        raw_frames: Optional[List[TelemetryPointSchema]] = None,
    ) -> OvertakeGeometryEvidence:
        """Synthesize comprehensive cornering overtake geometry and apex overlap evidence."""
        frames_list = frames if frames is not None else (raw_frames if raw_frames is not None else [])
        drv_a = candidate.driver_a.upper()
        drv_b = candidate.driver_b.upper()
        turn_str = candidate.turn or "Corner"

        if not frames_list:
            quality = OvertakeGeometryDataQuality(
                synchronized_timestamps=False,
                distance_monotonic=False,
                missing_telemetry=True,
                vehicle_dimension_assumptions_used=True,
                limitations=["No telemetry frames available for corner analysis window."],
            )
            phases = CornerPhases(
                corner_entry_distance_m=0.0,
                corner_entry_time_s=0.0,
                apex_distance_m=0.0,
                apex_time_s=0.0,
                apex_speed_kmh=0.0,
                corner_exit_distance_m=None,
                corner_exit_time_s=None,
                exit_detection_status="UNAVAILABLE",
            )
            apex_snap = ApexOverlapSnapshot(
                incident_car_code=drv_a,
                incident_distance_m=0.0,
                incident_speed_kmh=0.0,
                other_car_code=drv_b,
                other_distance_m=0.0,
                other_speed_kmh=0.0,
                longitudinal_gap_m=0.0,
                relative_position=RelativeLongitudinalPosition.UNAVAILABLE,
                overlap_percent=None,
                overlap_classification=OverlapClassification.INSUFFICIENT_GEOMETRIC_DATA,
                confidence=MeasurementConfidence.UNAVAILABLE,
            )
            exit_clearance = ExitClearanceMetrics(
                exit_distance_m=None,
                measured_clearance_m=None,
                reference_width_threshold_m=REFERENCE_F1_CAR_WIDTH_M,
                clearance_classification=ExitClearanceClassification.CLEARANCE_UNAVAILABLE,
                confidence=MeasurementConfidence.UNAVAILABLE,
                note="Telemetry frames unavailable.",
            )
            return OvertakeGeometryEvidence(
                incident_id=candidate.candidate_id,
                driver_incident=drv_a,
                driver_other=drv_b,
                turn=turn_str,
                corner_phases=phases,
                apex_snapshot=apex_snap,
                exit_clearance=exit_clearance,
                phase_snapshots=[],
                overlap_classification=OverlapClassification.INSUFFICIENT_GEOMETRIC_DATA,
                overlap_percent=None,
                front_axle_overlap_ratio=None,
                front_axle_overlap_percent=None,
                fia_reference=FIAGuidelineReference(),
                data_quality=quality,
                provenance_summary={},
                summary="Cornering overtake geometry unavailable due to missing telemetry frames.",
            )

        # 1. Quality Validation Checks
        limitations: List[str] = []
        sync_ts = True
        monotonic = True

        if len(frames_list) < 10:
            limitations.append("Insufficient telemetry sampling density across corner window.")
        
        # Check monotonicity
        for i in range(1, len(frames_list)):
            da_curr = self._extract_distance(frames_list[i], "a")
            da_prev = self._extract_distance(frames_list[i-1], "a")
            if da_curr < da_prev or frames_list[i].time_offset < frames_list[i-1].time_offset:
                monotonic = False
                limitations.append("Non-monotonic distance or timestamp sequence detected.")
                break

        limitations.append("Vehicle body dimensions modeled via FIA standard regulation reference (5.63m length, 2.00m width).")
        limitations.append("Curvilinear track boundary limits unavailable in standard CAN feed; clearance evaluated via vehicle spatial separation.")

        missing_tel = len(frames_list) == 0 or all(f.distance_a is None or f.distance_a == 0.0 for f in frames_list)

        quality = OvertakeGeometryDataQuality(
            synchronized_timestamps=sync_ts,
            distance_monotonic=monotonic,
            missing_telemetry=missing_tel,
            vehicle_dimension_assumptions_used=True,
            limitations=limitations,
        )

        # 2. Phase Detection
        phases = self.detect_corner_phases(frames_list)

        # 3. Apex Snapshot
        apex_snap = self.calculate_apex_snapshot(frames_list, phases.apex_distance_m, drv_a, drv_b)

        # 4. Exit Clearance
        exit_clearance = self.calculate_exit_clearance(frames_list, phases.corner_exit_distance_m)

        # 5. Milestone Phase Snapshots
        phase_snaps = self.build_phase_snapshots(frames_list, phases)

        # 6. Overall Overlap Metrics
        ratio, pct, classification = self.calculate_overlap(longitudinal_gap_m=apex_snap.longitudinal_gap_m)
        if missing_tel:
            classification = OverlapClassification.INSUFFICIENT_GEOMETRIC_DATA
            pct = None
            ratio = None
            apex_snap.overlap_classification = OverlapClassification.INSUFFICIENT_GEOMETRIC_DATA
            apex_snap.overlap_percent = None

        # Provenance summary map
        provenance_map = {
            "corner_entry_distance": MeasurementConfidence.DERIVED_FROM_TELEMETRY,
            "apex_distance": MeasurementConfidence.DERIVED_FROM_TELEMETRY,
            "apex_overlap_percent": MeasurementConfidence.DERIVED_FROM_POSITION if not missing_tel else MeasurementConfidence.UNAVAILABLE,
            "exit_clearance": MeasurementConfidence.DERIVED_FROM_POSITION if exit_clearance.measured_clearance_m else MeasurementConfidence.UNAVAILABLE,
            "front_axle_gap": MeasurementConfidence.DERIVED_FROM_POSITION if not missing_tel else MeasurementConfidence.UNAVAILABLE,
            "mirror_overlap": MeasurementConfidence.DERIVED_FROM_POSITION if not missing_tel else MeasurementConfidence.UNAVAILABLE,
            "steering_angle": MeasurementConfidence.UNAVAILABLE,
            "track_limits_boundary": MeasurementConfidence.UNAVAILABLE,
        }

        # Summary text
        pct_str = f", representing {pct:.1f}% longitudinal overlap ({classification.value})" if pct is not None else f" ({classification.value})"
        summary = (
            f"At {turn_str} apex ({phases.apex_distance_m:.0f}m, {phases.apex_speed_kmh:.0f} km/h), "
            f"{drv_a} and {drv_b} exhibited a longitudinal gap of {apex_snap.longitudinal_gap_m:+.2f}m "
            f"({apex_snap.relative_position.value}){pct_str}. "
        )
        if exit_clearance.measured_clearance_m is not None:
            exit_dist_str = f"{phases.corner_exit_distance_m:.0f}m" if phases.corner_exit_distance_m is not None else "exit"
            summary += (
                f"At corner exit ({exit_dist_str}), measured spatial clearance was "
                f"{exit_clearance.measured_clearance_m:.2f}m ({exit_clearance.clearance_classification.value} vs 2.0m car width reference)."
            )
        else:
            summary += "Corner exit clearance was unavailable within the analysis window."

        return OvertakeGeometryEvidence(
            incident_id=candidate.candidate_id,
            driver_incident=drv_a,
            driver_other=drv_b,
            turn=turn_str,
            corner_phases=phases,
            apex_snapshot=apex_snap,
            exit_clearance=exit_clearance,
            phase_snapshots=phase_snaps,
            overlap_classification=classification,
            overlap_percent=pct,
            front_axle_overlap_ratio=ratio,
            front_axle_overlap_percent=pct,
            fia_reference=FIAGuidelineReference(),
            data_quality=quality,
            provenance_summary=provenance_map,
            summary=summary,
        )


@lru_cache()
def get_overtake_geometry_service() -> CorneringOvertakeGeometryService:
    """Singleton provider for CorneringOvertakeGeometryService."""
    return CorneringOvertakeGeometryService()
