"""Reference-Lap Baseline and Incident Evidence Quantification Service.

Calculates deterministic reference-lap baselines and quantifies physical deviations
for incident candidates.

CRITICAL JURISPRUDENTIAL GUARDRAILS:
    1. NEVER assert guilt, fault, liability, or rule infringement.
    2. NEVER label trajectory deviation as proof of forcing another driver off-track.
    3. Explicitly report missing channels (steering angle, brake pressure, curvilinear coordinates)
       as UNAVAILABLE rather than inventing or interpolating them.
    4. Maintain FastF1 decimeter to meter conversion (SI meters).
"""

from functools import lru_cache
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from app.core.logging import logger
from app.data.domain import NormalizedLap, NormalizedTelemetryPoint
from app.evidence.baseline_models import (
    BaselineDisruptionMetrics,
    BaselineEvidence,
    BaselineProfilePoint,
    BaselineStatus,
    DriverBaselineEvidence,
    ReferenceLapProvenance,
    SignalProvenanceInfo,
    SignalStatus,
    TrajectoryDeviationMetrics,
)
from app.evidence.candidate import CandidateDossier
from app.schemas.telemetry import TelemetryPointSchema
from app.services.ingestion_service import get_ingestion_service


class ReferenceBaselineService:
    """Service providing reference-lap selection, distance alignment, and evidence quantification."""

    def __init__(self):
        self.ingestion = get_ingestion_service()

    # -------------------------------------------------------------------------
    # 1. Reference Lap Selection (Strict 7-Rule Implementation)
    # -------------------------------------------------------------------------

    def filter_reference_laps(
        self,
        laps: List[NormalizedLap],
        incident_lap: int,
        preferred_window: int = 6,
    ) -> Tuple[List[NormalizedLap], Dict[str, str]]:
        """Filter session laps using strict multi-criteria reference rules.

        Rules:
        1. Same session & driver (presupposed by caller input).
        2. Exclude incident lap.
        3. Exclude invalid laps or deleted lap times.
        4. Exclude out-laps and in-laps (missing sector times / pit stop entries).
        5. Exclude anomalous lap times (>110% or <85% of median lap time).
        6. Prefer clean laps within preferred window (+/- preferred_window laps).
        7. Minimum requirement of >= 2 clean reference laps.
        """
        excluded_reasons: Dict[str, str] = {}
        candidate_laps: List[NormalizedLap] = []

        # Gather valid timed laps to determine median lap pace
        timed_laps = [
            lap.lap_time_seconds
            for lap in laps
            if lap.lap_time_seconds is not None and lap.lap_time_seconds > 40.0
        ]
        median_time = float(np.median(timed_laps)) if timed_laps else None

        for lap in laps:
            lap_key = f"Lap {lap.lap_number}"

            # Rule 2: Exclude incident lap
            if lap.lap_number == incident_lap:
                excluded_reasons[lap_key] = "Incident lap"
                continue

            # Rule 3: Exclude invalid laps
            if not lap.is_valid:
                excluded_reasons[lap_key] = "Lap invalidated / deleted track limits"
                continue

            # Rule 4: Exclude laps without complete timing (out-laps / in-laps)
            if lap.lap_time_seconds is None or lap.lap_time_seconds <= 0.0:
                excluded_reasons[lap_key] = "Out-lap / In-lap / pit transit"
                continue

            # Rule 5: Exclude lap time pace anomalies (safety car, yellow flags, pit in/out)
            if median_time is not None:
                if lap.lap_time_seconds > 1.10 * median_time:
                    delta = lap.lap_time_seconds - median_time
                    excluded_reasons[lap_key] = f"Lap pace anomaly (+{delta:.1f}s vs median, likely SC/VSC/pit)"
                    continue
                if lap.lap_time_seconds < 0.85 * median_time:
                    excluded_reasons[lap_key] = "Unphysically short lap time"
                    continue

            candidate_laps.append(lap)

        # Rule 6: Prioritize laps within proximity window (+/- preferred_window)
        close_laps = [
            lap for lap in candidate_laps
            if abs(lap.lap_number - incident_lap) <= preferred_window
        ]
        
        # If we have >= 2 close laps, use them for closer tire/fuel condition matching
        if len(close_laps) >= 2:
            final_laps = close_laps
            # Note non-selected laps outside window
            for lap in candidate_laps:
                if lap not in close_laps:
                    excluded_reasons[f"Lap {lap.lap_number}"] = f"Outside preferred proximity window (+/-{preferred_window} laps)"
        else:
            final_laps = candidate_laps

        return final_laps, excluded_reasons

    # -------------------------------------------------------------------------
    # 2. Distance Grid Resampling and Alignment
    # -------------------------------------------------------------------------

    def align_telemetry_on_distance(
        self,
        points: List[NormalizedTelemetryPoint],
        s_start: float,
        s_end: float,
        step_m: float = 2.0,
    ) -> Optional[Dict[str, np.ndarray]]:
        """Resample a single lap's telemetry onto a uniform distance grid."""
        if not points or s_end <= s_start:
            return None

        # Sort by distance and filter out None distance frames
        valid_pts = [p for p in points if p.distance is not None]
        if len(valid_pts) < 5:
            return None

        valid_pts.sort(key=lambda p: p.distance)

        # Remove duplicate distances for monotonic interpolation
        dists: List[float] = []
        speeds: List[float] = []
        throttles: List[float] = []
        brakes: List[float] = []
        xs: List[float] = []
        ys: List[float] = []
        times: List[float] = []

        last_d = -1e9
        for p in valid_pts:
            d = float(p.distance)
            if d > last_d:
                dists.append(d)
                speeds.append(float(p.speed) if p.speed is not None else 0.0)
                throttles.append(float(p.throttle) if p.throttle is not None else 0.0)
                brakes.append(float(p.brake) if p.brake is not None else 0.0)
                xs.append(float(p.x) if p.x is not None else np.nan)
                ys.append(float(p.y) if p.y is not None else np.nan)
                times.append(float(p.time_offset))
                last_d = d

        if not dists or dists[0] > s_start or dists[-1] < s_end:
            # Distance range does not fully cover the window
            # Clamp grid bounds to available coverage if within 20m tolerance
            s_min_avail = max(s_start, dists[0])
            s_max_avail = min(s_end, dists[-1])
            if s_max_avail - s_min_avail < 50.0:
                return None
            grid = np.arange(s_min_avail, s_max_avail + step_m, step_m)
        else:
            grid = np.arange(s_start, s_end + step_m, step_m)

        if len(grid) < 5:
            return None

        dists_arr = np.array(dists)
        res_speed = np.interp(grid, dists_arr, speeds)
        res_throttle = np.interp(grid, dists_arr, throttles)
        res_brake = np.interp(grid, dists_arr, brakes)
        res_time = np.interp(grid, dists_arr, times)

        # Interpolate coordinates if present
        has_coords = not (np.isnan(xs).all() or np.isnan(ys).all())
        if has_coords:
            valid_x = np.nan_to_num(xs, nan=0.0)
            valid_y = np.nan_to_num(ys, nan=0.0)
            res_x = np.interp(grid, dists_arr, valid_x)
            res_y = np.interp(grid, dists_arr, valid_y)
        else:
            res_x = np.zeros_like(grid)
            res_y = np.zeros_like(grid)

        return {
            "distance": grid,
            "speed": res_speed,
            "throttle": res_throttle,
            "brake": res_brake,
            "x": res_x,
            "y": res_y,
            "time_offset": res_time,
            "has_coords": has_coords,
        }

    # -------------------------------------------------------------------------
    # 3. Robust Median Baseline Computation
    # -------------------------------------------------------------------------

    def compute_median_baseline(
        self,
        aligned_laps: List[Dict[str, np.ndarray]],
        distance_grid: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        """Compute pointwise median across reference laps for uniform distance grid."""
        n_laps = len(aligned_laps)
        grid_len = len(distance_grid)

        speed_mat = np.zeros((n_laps, grid_len))
        throttle_mat = np.zeros((n_laps, grid_len))
        brake_mat = np.zeros((n_laps, grid_len))
        x_mat = np.zeros((n_laps, grid_len))
        y_mat = np.zeros((n_laps, grid_len))
        time_mat = np.zeros((n_laps, grid_len))

        has_coords = any(lap.get("has_coords", False) for lap in aligned_laps)

        for i, lap in enumerate(aligned_laps):
            lap_grid = lap["distance"]
            # Interpolate to target distance_grid if small boundary variations exist
            speed_mat[i] = np.interp(distance_grid, lap_grid, lap["speed"])
            throttle_mat[i] = np.interp(distance_grid, lap_grid, lap["throttle"])
            brake_mat[i] = np.interp(distance_grid, lap_grid, lap["brake"])
            time_mat[i] = np.interp(distance_grid, lap_grid, lap["time_offset"])
            if has_coords:
                x_mat[i] = np.interp(distance_grid, lap_grid, lap["x"])
                y_mat[i] = np.interp(distance_grid, lap_grid, lap["y"])

        median_speed = np.median(speed_mat, axis=0)
        speed_iqr = np.percentile(speed_mat, 75, axis=0) - np.percentile(speed_mat, 25, axis=0)

        median_throttle = np.median(throttle_mat, axis=0)
        median_brake = np.median(brake_mat, axis=0)
        median_time = np.median(time_mat, axis=0)

        median_x = np.median(x_mat, axis=0) if has_coords else np.zeros(grid_len)
        median_y = np.median(y_mat, axis=0) if has_coords else np.zeros(grid_len)

        return {
            "distance": distance_grid,
            "speed": median_speed,
            "speed_iqr": speed_iqr,
            "throttle": median_throttle,
            "brake": median_brake,
            "x": median_x,
            "y": median_y,
            "time_offset": median_time,
            "has_coords": has_coords,
        }

    # -------------------------------------------------------------------------
    # 4. Disruption Metrics Quantification
    # -------------------------------------------------------------------------

    def compute_disruption_metrics(
        self,
        baseline: Dict[str, np.ndarray],
        incident: Dict[str, np.ndarray],
        driver_code: str,
    ) -> BaselineDisruptionMetrics:
        """Compute empirical delta metrics between incident and reference baseline."""
        grid = baseline["distance"]
        b_speed = baseline["speed"]
        i_speed = incident["speed"]
        b_brake = baseline["brake"]
        i_brake = incident["brake"]
        b_throttle = baseline["throttle"]
        i_throttle = incident["throttle"]

        # 1. Apex (minimum speed) identification
        b_apex_idx = int(np.argmin(b_speed))
        i_apex_idx = int(np.argmin(i_speed))

        speed_apex_base = round(float(b_speed[b_apex_idx]), 1)
        speed_apex_inc = round(float(i_speed[i_apex_idx]), 1)
        min_corner_speed_delta = round(speed_apex_inc - speed_apex_base, 1)

        # 2. Braking onset identification (first point with brake >= 10% or throttle <= 20% before apex)
        def find_braking_onset(brake_arr: np.ndarray, throttle_arr: np.ndarray, apex_idx: int) -> int:
            for idx in range(min(apex_idx, len(brake_arr))):
                if brake_arr[idx] >= 10.0 or throttle_arr[idx] <= 20.0:
                    return idx
            return 0

        b_brake_idx = find_braking_onset(b_brake, b_throttle, b_apex_idx)
        i_brake_idx = find_braking_onset(i_brake, i_throttle, i_apex_idx)

        b_brake_dist = float(grid[b_brake_idx])
        i_brake_dist = float(grid[i_brake_idx])
        braking_onset_delta_m = round(i_brake_dist - b_brake_dist, 1)

        # Convert distance delta to time delta using approach speed
        approach_speed_ms = max(float(b_speed[0]) / 3.6, 20.0)
        braking_onset_delta_sec = round(braking_onset_delta_m / approach_speed_ms, 3)

        # 3. Peak brake delta in braking zone
        b_peak_brake = float(np.max(b_brake[: b_apex_idx + 1])) if b_apex_idx > 0 else float(np.max(b_brake))
        i_peak_brake = float(np.max(i_brake[: i_apex_idx + 1])) if i_apex_idx > 0 else float(np.max(i_brake))
        peak_brake_delta = round(i_peak_brake - b_peak_brake, 1)

        # 4. Throttle lift offset (first drop below 95% throttle)
        def find_throttle_lift(throttle_arr: np.ndarray, apex_idx: int) -> int:
            for idx in range(min(apex_idx, len(throttle_arr))):
                if throttle_arr[idx] < 95.0:
                    return idx
            return 0

        b_lift_idx = find_throttle_lift(b_throttle, b_apex_idx)
        i_lift_idx = find_throttle_lift(i_throttle, i_apex_idx)
        throttle_lift_delta_m = round(float(grid[i_lift_idx]) - float(grid[b_lift_idx]), 1)

        # 5. Throttle reapplication delay (distance from apex until throttle >= 50%)
        def find_reapplication(throttle_arr: np.ndarray, apex_idx: int) -> int:
            for idx in range(apex_idx, len(throttle_arr)):
                if throttle_arr[idx] >= 50.0:
                    return idx
            return len(throttle_arr) - 1

        b_reapp_idx = find_reapplication(b_throttle, b_apex_idx)
        i_reapp_idx = find_reapplication(i_throttle, i_apex_idx)

        b_delay_m = float(grid[b_reapp_idx]) - float(grid[b_apex_idx])
        i_delay_m = float(grid[i_reapp_idx]) - float(grid[i_apex_idx])
        throttle_reapplication_delay_m = round(i_delay_m - b_delay_m, 1)

        exit_speed_ms = max(speed_apex_base / 3.6, 15.0)
        throttle_reapplication_delay_sec = round(throttle_reapplication_delay_m / exit_speed_ms, 3)

        return BaselineDisruptionMetrics(
            driver_code=driver_code,
            braking_onset_delta_m=braking_onset_delta_m,
            braking_onset_delta_sec=braking_onset_delta_sec,
            peak_brake_pct_delta=peak_brake_delta,
            throttle_lift_delta_m=throttle_lift_delta_m,
            throttle_reapplication_delay_m=throttle_reapplication_delay_m,
            throttle_reapplication_delay_sec=throttle_reapplication_delay_sec,
            min_corner_speed_delta_kmh=min_corner_speed_delta,
            speed_at_apex_incident_kmh=speed_apex_inc,
            speed_at_apex_baseline_kmh=speed_apex_base,
        )

    # -------------------------------------------------------------------------
    # 5. Trajectory Deviation Quantification
    # -------------------------------------------------------------------------

    def compute_trajectory_deviation(
        self,
        baseline: Dict[str, np.ndarray],
        incident: Dict[str, np.ndarray],
        driver_code: str,
    ) -> TrajectoryDeviationMetrics:
        """Compute Cartesian Euclidean trajectory deviation metrics relative to baseline."""
        has_coords = baseline.get("has_coords", False) and incident.get("has_coords", False)
        
        if not has_coords:
            return TrajectoryDeviationMetrics(
                driver_code=driver_code,
                status=SignalStatus.UNAVAILABLE,
                max_trajectory_deviation_m=0.0,
                mean_trajectory_deviation_m=0.0,
                deviation_at_apex_m=None,
                note="Cartesian spatial coordinates (X, Y) were unavailable or degenerate for this session segment.",
            )

        dx = incident["x"] - baseline["x"]
        dy = incident["y"] - baseline["y"]
        dev_m = np.sqrt(dx**2 + dy**2)

        max_dev = round(float(np.max(dev_m)), 2)
        mean_dev = round(float(np.mean(dev_m)), 2)

        # Deviation at baseline corner apex
        b_apex_idx = int(np.argmin(baseline["speed"]))
        dev_apex = round(float(dev_m[b_apex_idx]), 2) if b_apex_idx < len(dev_m) else None

        return TrajectoryDeviationMetrics(
            driver_code=driver_code,
            status=SignalStatus.DERIVED,
            max_trajectory_deviation_m=max_dev,
            mean_trajectory_deviation_m=mean_dev,
            deviation_at_apex_m=dev_apex,
            lateral_track_deviation_status=SignalStatus.UNAVAILABLE,
            note="Computed via 2D Cartesian Euclidean distance (X, Y in SI meters after decimeter conversion). "
            "Track-relative curvilinear coordinate (d) is UNAVAILABLE in standard FastF1 telemetry.",
        )

    # -------------------------------------------------------------------------
    # 6. Profile Sampling
    # -------------------------------------------------------------------------

    def build_profile_sample(
        self,
        baseline: Dict[str, np.ndarray],
        incident: Dict[str, np.ndarray],
        max_samples: int = 25,
    ) -> List[BaselineProfilePoint]:
        """Generate uniform distance sample points comparing incident vs baseline."""
        grid = baseline["distance"]
        n_points = len(grid)
        step = max(1, n_points // max_samples)
        indices = list(range(0, n_points, step))
        if (n_points - 1) not in indices:
            indices.append(n_points - 1)

        has_coords = baseline.get("has_coords", False) and incident.get("has_coords", False)

        profiles: List[BaselineProfilePoint] = []
        for idx in indices:
            d = round(float(grid[idx]), 1)
            b_spd = round(float(baseline["speed"][idx]), 1)
            i_spd = round(float(incident["speed"][idx]), 1)
            d_spd = round(i_spd - b_spd, 1)
            iqr_spd = round(float(baseline["speed_iqr"][idx]), 1)

            b_thr = round(float(baseline["throttle"][idx]), 1)
            i_thr = round(float(incident["throttle"][idx]), 1)
            d_thr = round(i_thr - b_thr, 1)

            b_brk = round(float(baseline["brake"][idx]), 1)
            i_brk = round(float(incident["brake"][idx]), 1)
            d_brk = round(i_brk - b_brk, 1)

            if has_coords:
                x_b = round(float(baseline["x"][idx]), 2)
                y_b = round(float(baseline["y"][idx]), 2)
                x_i = round(float(incident["x"][idx]), 2)
                y_i = round(float(incident["y"][idx]), 2)
                traj_dev = round(math.sqrt((x_i - x_b)**2 + (y_i - y_b)**2), 2)
            else:
                x_b = y_b = x_i = y_i = traj_dev = None

            profiles.append(
                BaselineProfilePoint(
                    distance_m=d,
                    speed_baseline_kmh=b_spd,
                    speed_incident_kmh=i_spd,
                    speed_delta_kmh=d_spd,
                    speed_iqr_kmh=iqr_spd,
                    throttle_baseline_pct=b_thr,
                    throttle_incident_pct=i_thr,
                    throttle_delta_pct=d_thr,
                    brake_baseline_pct=b_brk,
                    brake_incident_pct=i_brk,
                    brake_delta_pct=d_brk,
                    x_baseline_m=x_b,
                    y_baseline_m=y_b,
                    x_incident_m=x_i,
                    y_incident_m=y_i,
                    trajectory_deviation_m=traj_dev,
                )
            )

        return profiles

    # -------------------------------------------------------------------------
    # 7. End-to-End Driver Baseline Quantification
    # -------------------------------------------------------------------------

    def quantify_driver(
        self,
        driver_code: str,
        incident_lap: int,
        incident_points: List[NormalizedTelemetryPoint],
        session_laps: List[NormalizedLap],
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        step_m: float = 2.0,
    ) -> DriverBaselineEvidence:
        """Execute reference-lap selection, distance alignment, and quantification for one driver."""
        drv_upper = driver_code.upper()
        drv_laps = [lap for lap in session_laps if lap.driver_code.upper() == drv_upper]

        # 1. Filter reference laps
        valid_ref_laps, exclusions = self.filter_reference_laps(
            laps=drv_laps,
            incident_lap=incident_lap,
        )

        provenance = ReferenceLapProvenance(
            driver_code=drv_upper,
            reference_laps_used=[lap.lap_number for lap in valid_ref_laps],
            total_laps_analyzed=len(drv_laps),
            excluded_laps_reasons=exclusions,
            aggregation_method="Pointwise median across uniform 2.0m distance grid with IQR variability",
            resampling_resolution_m=step_m,
        )

        # Check sufficiency (minimum 2 laps)
        if len(valid_ref_laps) < 2:
            return DriverBaselineEvidence(
                driver_code=drv_upper,
                status=BaselineStatus.INSUFFICIENT_REFERENCE_DATA,
                provenance=provenance,
                disruption_metrics=None,
                trajectory_metrics=None,
                profile_sample=[],
                notes=[
                    f"Insufficient clean reference laps for {drv_upper} in session ({len(valid_ref_laps)} available, minimum 2 required).",
                    "Lap 1 incidents or sessions with frequent safety cars/retirements may lack adequate steady-state reference laps.",
                ],
            )

        # 2. Determine distance window from incident points
        valid_inc_pts = [p for p in incident_points if p.distance is not None]
        if not valid_inc_pts:
            return DriverBaselineEvidence(
                driver_code=drv_upper,
                status=BaselineStatus.ALIGNMENT_FAILED,
                provenance=provenance,
                notes=["Incident telemetry has no valid distance channel for spatial alignment."],
            )

        s_start = min(float(p.distance) for p in valid_inc_pts)
        s_end = max(float(p.distance) for p in valid_inc_pts)

        # Pad by 30 meters if window is very short
        if s_end - s_start < 60.0:
            s_start = max(0.0, s_start - 30.0)
            s_end = s_end + 30.0

        # 3. Align incident telemetry
        incident_aligned = self.align_telemetry_on_distance(
            points=valid_inc_pts,
            s_start=s_start,
            s_end=s_end,
            step_m=step_m,
        )

        if not incident_aligned:
            return DriverBaselineEvidence(
                driver_code=drv_upper,
                status=BaselineStatus.ALIGNMENT_FAILED,
                provenance=provenance,
                notes=["Failed to align incident telemetry to distance grid."],
            )

        dist_grid = incident_aligned["distance"]

        # 4. Ingest and align reference lap telemetry
        aligned_ref_laps: List[Dict[str, np.ndarray]] = []
        for lap in valid_ref_laps:
            try:
                raw_ref_tel = self.ingestion.load_driver_telemetry(
                    season=season,
                    round_or_name=round_or_name,
                    session_identifier=session_identifier,
                    driver=drv_upper,
                    lap=lap.lap_number,
                )
                aligned = self.align_telemetry_on_distance(
                    points=raw_ref_tel,
                    s_start=dist_grid[0],
                    s_end=dist_grid[-1],
                    step_m=step_m,
                )
                if aligned is not None:
                    aligned_ref_laps.append(aligned)
            except Exception as e:
                logger.warning(f"Failed loading ref lap {lap.lap_number} for {drv_upper}: {e}")
                exclusions[f"Lap {lap.lap_number}"] = f"Telemetry load failure: {str(e)}"

        if len(aligned_ref_laps) < 2:
            provenance.reference_laps_used = [l.get("lap", 0) for l in aligned_ref_laps]
            return DriverBaselineEvidence(
                driver_code=drv_upper,
                status=BaselineStatus.INSUFFICIENT_REFERENCE_DATA,
                provenance=provenance,
                notes=[f"Fewer than 2 reference laps had valid telemetry covering the distance window [{s_start:.0f}m, {s_end:.0f}m]."],
            )

        # 5. Compute robust baseline
        baseline = self.compute_median_baseline(aligned_ref_laps, dist_grid)

        # 6. Quantify disruption and trajectory metrics
        disruption = self.compute_disruption_metrics(baseline, incident_aligned, drv_upper)
        trajectory = self.compute_trajectory_deviation(baseline, incident_aligned, drv_upper)
        profile_sample = self.build_profile_sample(baseline, incident_aligned)

        notes = [
            f"Baseline constructed from {len(aligned_ref_laps)} clean laps (Laps: {provenance.reference_laps_used}).",
            f"Distance window: {dist_grid[0]:.1f}m to {dist_grid[-1]:.1f}m ({dist_grid[-1] - dist_grid[0]:.1f}m window).",
        ]
        if trajectory.deviation_at_apex_m is not None:
            notes.append(f"Apex trajectory deviation: {trajectory.deviation_at_apex_m:.2f}m.")

        return DriverBaselineEvidence(
            driver_code=drv_upper,
            status=BaselineStatus.AVAILABLE,
            provenance=provenance,
            disruption_metrics=disruption,
            trajectory_metrics=trajectory,
            profile_sample=profile_sample,
            notes=notes,
        )

    # -------------------------------------------------------------------------
    # 8. Full Incident Candidate Evidence Synthesis
    # -------------------------------------------------------------------------

    def synthesize_baseline_evidence(
        self,
        candidate: CandidateDossier,
        raw_frames: List[TelemetryPointSchema],
        season: int = 2024,
        round_or_name: Union[int, str] = "Monza",
        session: str = "Race",
    ) -> BaselineEvidence:
        """Synthesize reference-lap baseline evidence for both drivers in a candidate incident."""
        drv_a = candidate.driver_a.upper()
        drv_b = candidate.driver_b.upper()
        lap_a = candidate.lap_number_a or 1
        lap_b = candidate.lap_number_b or 1

        # Extract incident driver telemetry from raw_frames
        pts_a: List[NormalizedTelemetryPoint] = []
        pts_b: List[NormalizedTelemetryPoint] = []

        for f in raw_frames:
            pts_a.append(
                NormalizedTelemetryPoint(
                    time_offset=f.time_offset,
                    driver_code=drv_a,
                    lap_number=lap_a,
                    distance=f.distance_a,
                    speed=f.speed_a,
                    throttle=f.throttle_a,
                    brake=f.brake_a,
                    gear=f.gear_a,
                    x=f.x_a if hasattr(f, "x_a") and f.x_a is not None else None,
                    y=f.y_a if hasattr(f, "y_a") and f.y_a is not None else None,
                )
            )
            pts_b.append(
                NormalizedTelemetryPoint(
                    time_offset=f.time_offset,
                    driver_code=drv_b,
                    lap_number=lap_b,
                    distance=f.distance_b,
                    speed=f.speed_b,
                    throttle=f.throttle_b,
                    brake=f.brake_b,
                    gear=f.gear_b,
                    x=f.x_b if hasattr(f, "x_b") and f.x_b is not None else None,
                    y=f.y_b if hasattr(f, "y_b") and f.y_b is not None else None,
                )
            )

        # Load session laps
        try:
            session_laps = self.ingestion.load_session_laps(
                season=season,
                round_or_name=round_or_name,
                session_identifier=session,
            )
        except Exception as e:
            logger.warning(f"Could not load session laps: {e}")
            session_laps = []

        # Quantify for Driver A
        evidence_a = self.quantify_driver(
            driver_code=drv_a,
            incident_lap=lap_a,
            incident_points=pts_a,
            session_laps=session_laps,
            season=season,
            round_or_name=round_or_name,
            session_identifier=session,
        )

        # Quantify for Driver B
        evidence_b = self.quantify_driver(
            driver_code=drv_b,
            incident_lap=lap_b,
            incident_points=pts_b,
            session_laps=session_laps,
            season=season,
            round_or_name=round_or_name,
            session_identifier=session,
        )

        drivers_map = {
            drv_a: evidence_a,
            drv_b: evidence_b,
        }

        overall_status = (
            BaselineStatus.AVAILABLE
            if evidence_a.status == BaselineStatus.AVAILABLE or evidence_b.status == BaselineStatus.AVAILABLE
            else BaselineStatus.INSUFFICIENT_REFERENCE_DATA
        )

        # Build summary
        summary_parts = []
        for code, ev in [(drv_a, evidence_a), (drv_b, evidence_b)]:
            if ev.status == BaselineStatus.AVAILABLE and ev.disruption_metrics:
                m = ev.disruption_metrics
                t = ev.trajectory_metrics
                traj_str = f"Max trajectory deviation: {t.max_trajectory_deviation_m:.2f}m." if t else ""
                summary_parts.append(
                    f"{code}: Min corner speed delta: {m.min_corner_speed_delta_kmh:+.1f} km/h "
                    f"(apex: {m.speed_at_apex_incident_kmh:.0f} vs base: {m.speed_at_apex_baseline_kmh:.0f} km/h). "
                    f"Braking onset delta: {m.braking_onset_delta_m:+.1f}m. {traj_str}"
                )
            else:
                summary_parts.append(f"{code}: Baseline reference unavailable ({ev.status.value}).")

        summary = " ".join(summary_parts)

        return BaselineEvidence(
            status=overall_status,
            drivers=drivers_map,
            summary=summary,
            signal_provenance=SignalProvenanceInfo(),
        )


@lru_cache()
def get_baseline_service() -> ReferenceBaselineService:
    """Singleton provider for ReferenceBaselineService."""
    return ReferenceBaselineService()
