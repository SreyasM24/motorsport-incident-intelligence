"""Cross-Modal Consistency & Discrepancy Analysis Engine.

Performs deterministic cross-modal checks between telemetry, baseline, geometry,
video, visual, and computer vision evidence streams.
"""

from typing import Dict, List, Optional, Tuple

from app.evidence.synthesis.contracts import (
    ConsistencyStatus,
    CrossModalDiscrepancy,
    DiscrepancySeverity,
    EvidenceConsensus,
    EvidenceItem,
    EvidenceStatus,
    EvidenceType,
)
from app.evidence.synthesis.lineage import LineageTracker


class ConsistencyEngine:
    """Evaluates cross-stream consistency and identifies empirical discrepancies."""

    @staticmethod
    def analyze_cross_modal_consistency(
        candidate_id: str,
        items: List[EvidenceItem],
        telemetry_min_gap_m: float,
        telemetry_event_time_sec: float,
        visual_min_sep_sec: Optional[float] = None,
        sync_uncertainty_sec: float = 0.05,
        video_available: bool = False,
        cv_available: bool = False,
        apex_overlap_pct: Optional[float] = None,
        apex_longitudinal_gap_m: Optional[float] = None,
        braking_onset_delta_m: Optional[float] = None,
    ) -> Tuple[ConsistencyStatus, EvidenceConsensus, List[CrossModalDiscrepancy]]:
        """Run deterministic consistency checks across all available evidence streams.

        CRITICAL GUARDRAIL:
            Discrepancies and severities are technical/empirical alignment indicators.
            They are NEVER interpreted as evidence of driver fault or sporting guilt.
        """
        discrepancies: List[CrossModalDiscrepancy] = []
        supporting: List[str] = []
        conflicting: List[str] = []
        unavailable: List[str] = []

        # 1. Telemetry Stream
        supporting.append("TELEMETRY")

        # 2. Reference Baseline Braking Discrepancy Check
        if braking_onset_delta_m is not None:
            supporting.append("REFERENCE_BASELINE")
            if abs(braking_onset_delta_m) > 15.0:
                discrepancies.append(
                    CrossModalDiscrepancy(
                        discrepancy_id=f"DISC-{candidate_id}-01-BRAKE",
                        evidence_stream_a="INCIDENT_TELEMETRY",
                        evidence_stream_b="REFERENCE_BASELINE",
                        metric="Braking Onset Location Delta",
                        observed_difference=f"{braking_onset_delta_m:+.1f} meters",
                        expected_tolerance="±10.0 meters",
                        severity=DiscrepancySeverity.MEDIUM,
                        status="OPEN",
                        explanation=(
                            f"Incident braking initiation occurred {abs(braking_onset_delta_m):.1f}m "
                            f"{'later' if braking_onset_delta_m > 0 else 'earlier'} than the clean reference lap baseline."
                        ),
                        provenance="Pointwise Median Reference Lap Comparison",
                    )
                )

        # 3. Geometry Apex Overlap vs Telemetry Gap Check
        if apex_overlap_pct is not None and apex_longitudinal_gap_m is not None:
            supporting.append("OVERTAKE_GEOMETRY")
            # If geometry indicates >50% overlap but longitudinal gap > 3.0m (half a car length without overlap)
            if apex_overlap_pct >= 50.0 and apex_longitudinal_gap_m > 3.0:
                discrepancies.append(
                    CrossModalDiscrepancy(
                        discrepancy_id=f"DISC-{candidate_id}-02-GEOM",
                        evidence_stream_a="OVERTAKE_GEOMETRY",
                        evidence_stream_b="RAW_TELEMETRY_COORDINATES",
                        metric="Apex Longitudinal Alignment",
                        observed_difference=f"{apex_overlap_pct:.1f}% overlap vs {apex_longitudinal_gap_m:.2f}m longitudinal separation",
                        expected_tolerance="Overlap >=50% implies longitudinal gap <= 2.80m",
                        severity=DiscrepancySeverity.HIGH,
                        status="INVESTIGATING",
                        explanation=(
                            "Potential geometric coordinate re-projection tension between vehicle dimension "
                            "envelope assumptions and Cartesian GPS distance."
                        ),
                        provenance="OvertakeGeometryService",
                    )
                )
                conflicting.append("OVERTAKE_GEOMETRY")

        # 4. Telemetry vs Video / Visual Temporal Synchronization Check
        if not video_available:
            unavailable.append("VIDEO_SYNCHRONIZATION")
            discrepancies.append(
                CrossModalDiscrepancy(
                    discrepancy_id=f"DISC-{candidate_id}-03-VID-UNAVAIL",
                    evidence_stream_a="TELEMETRY_EVENT_ANCHOR",
                    evidence_stream_b="BROADCAST_VIDEO",
                    metric="Visual Video Linkage",
                    observed_difference="Video Stream Unlinked",
                    expected_tolerance="Synchronized Frame-Accurate Timecode",
                    severity=DiscrepancySeverity.UNRESOLVED,
                    status="UNRESOLVED",
                    explanation=(
                        "Official race broadcast footage is commercially copyrighted and unlinked. "
                        "Visual cross-modal temporal alignment cannot be evaluated."
                    ),
                    provenance="Commercial Licensing / FOM Broadcast Policy",
                )
            )
        else:
            supporting.append("VIDEO_SYNCHRONIZATION")
            if visual_min_sep_sec is not None:
                delta_sec = abs(visual_min_sep_sec - telemetry_event_time_sec)
                if delta_sec > 0.20 + sync_uncertainty_sec:
                    discrepancies.append(
                        CrossModalDiscrepancy(
                            discrepancy_id=f"DISC-{candidate_id}-04-VIS-DELTA",
                            evidence_stream_a="TELEMETRY_PEAK_PROXIMITY",
                            evidence_stream_b="VISUAL_MIN_SEPARATION",
                            metric="Cross-Modal Temporal Disparity",
                            observed_difference=f"{delta_sec:.3f} seconds",
                            expected_tolerance="±0.200 seconds",
                            severity=DiscrepancySeverity.HIGH,
                            status="OPEN",
                            explanation=(
                                f"Disparity of {delta_sec:.3f}s between telemetry minimum gap and visual "
                                "minimum image-plane separation exceeds synchronization tolerance."
                            ),
                            provenance="VisualKeyframeExtractor",
                        )
                    )
                    conflicting.append("VISUAL")
                elif delta_sec > 0.20:
                    discrepancies.append(
                        CrossModalDiscrepancy(
                            discrepancy_id=f"DISC-{candidate_id}-04-VIS-DELTA",
                            evidence_stream_a="TELEMETRY_PEAK_PROXIMITY",
                            evidence_stream_b="VISUAL_MIN_SEPARATION",
                            metric="Cross-Modal Temporal Disparity",
                            observed_difference=f"{delta_sec:.3f} seconds",
                            expected_tolerance="±0.200 seconds",
                            severity=DiscrepancySeverity.MEDIUM,
                            status="OPEN",
                            explanation="Temporal disparity is within synchronization uncertainty margin (±0.05s).",
                            provenance="VisualKeyframeExtractor",
                        )
                    )

        # 5. Computer Vision Stream
        if not cv_available:
            unavailable.append("COMPUTER_VISION")
        else:
            supporting.append("COMPUTER_VISION")

        # 6. Overall Cross-Modal Consistency Status
        if conflicting:
            consistency = ConsistencyStatus.CONFLICTING
        elif not video_available and not cv_available:
            consistency = ConsistencyStatus.INSUFFICIENT_DATA
        elif any(d.severity in [DiscrepancySeverity.HIGH, DiscrepancySeverity.MEDIUM] for d in discrepancies):
            consistency = ConsistencyStatus.PARTIALLY_CONSISTENT
        else:
            consistency = ConsistencyStatus.CONSISTENT

        # 7. Independent Observation Count (Double-Counting Prevention)
        indep_count = LineageTracker.compute_independent_observation_count(items)

        # 8. Fact-Based Consensus Statement (NO single AI composite score!)
        supporting_str = ", ".join(supporting) if supporting else "None"
        unavailable_str = ", ".join(unavailable) if unavailable else "None"
        conflicting_str = ", ".join(conflicting) if conflicting else "None"

        summary = (
            f"Evidence synthesis identified {len(supporting)} supporting streams ({supporting_str}), "
            f"{len(conflicting)} conflicting streams ({conflicting_str}), and "
            f"{len(unavailable)} unavailable streams ({unavailable_str}). "
            f"Consensus is evaluated across {indep_count} independent empirical observation roots."
        )

        guidance = (
            "STEWARD GUIDANCE: Evaluate telemetry proximity traces alongside overtake geometry clearance. "
            "Where video/CV is unavailable, missing evidence must be treated as unobserved rather than negative evidence. "
            "No single automated score or verdict is issued."
        )

        consensus = EvidenceConsensus(
            supporting_evidence_streams=supporting,
            conflicting_evidence_streams=conflicting,
            unavailable_evidence_streams=unavailable,
            independent_observation_count=indep_count,
            total_evidence_items=len(items),
            consensus_summary=summary,
            steward_inspection_guidance=guidance,
        )

        return consistency, consensus, discrepancies
