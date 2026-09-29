"""Unified multi-modal incident evidence dossier.

Synthesizes telemetry, race control notices, video synchronization metadata,
statutory regulation provisions, and chronological event timelines into a
verifiable, neutral steward evidence dossier.

CRITICAL JURISPRUDENTIAL DOCTRINE:
    This dossier provides empirical evidence intelligence for human stewards.
    It DOES NOT decide guilt, fault, penalty, or automated adjudication.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.evidence.baseline_models import BaselineEvidence, BaselineStatus
from app.schemas.overtake_geometry import OvertakeGeometryEvidence
from app.schemas.ml_evidence import MLEvidence
from app.ml.features import extract_features_from_dossier_data
from app.ml.models import get_candidate_classifier
from app.evidence.candidate import (
    CandidateDossier,
    CandidateEventType,
    CandidateStatus,
    DataQualityFlags,
)
from app.evidence.provenance import EvidenceProvenanceRecord, build_default_provenance
from app.evidence.race_control_evidence import (
    RaceControlEvidenceSummary,
    build_race_control_evidence,
)
from app.evidence.regulation_evidence import (
    RegulationEvidenceSummary,
    match_relevant_regulations,
)
from app.evidence.telemetry_evidence import (
    TelemetryEvidenceSummary,
    build_telemetry_evidence,
)
from app.evidence.timeline import TimelineMilestone, generate_event_timeline
from app.evidence.video_evidence import (
    VideoEvidenceSummary,
    VideoSourceMetadata,
    VideoSyncStatus,
    build_video_evidence,
)
from app.evidence.visual import (
    VisualEvidenceSummary,
    VisualObservationStatus,
)
from app.schemas.incident import (
    EvidenceItemSchema,
    EvidenceRegulationConnectionSchema,
    EvidenceSources,
    IncidentDetailResponse,
    IncidentTimelineMilestoneSchema,
    TimeWindow,
)
from app.schemas.regulation import RelevantRegulationSchema
from app.schemas.telemetry import TelemetryPointSchema


class EvidenceDimensions(BaseModel):
    """Explicitly decoupled multi-dimensional evidence confidence indicators."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    telemetry_evidence_strength: int = Field(..., ge=0, le=100, description="Telemetry sensor convergence (0-100)")
    race_control_context_strength: int = Field(..., ge=0, le=100, description="Race control correlation (0-100)")
    video_evidence_status: VideoSyncStatus
    regulation_reference_status: str


class IncidentEvidenceDossier(BaseModel):
    """The master multi-modal incident evidence dossier for human steward investigation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    dossier_id: str
    candidate_id: str
    session_id: str
    event_type: CandidateEventType
    status: CandidateStatus = CandidateStatus.PENDING_REVIEW

    # Core multi-modal evidence components
    candidate: CandidateDossier
    telemetry_evidence: TelemetryEvidenceSummary
    timeline: List[TimelineMilestone] = Field(default_factory=list)
    race_control_evidence: RaceControlEvidenceSummary
    video_evidence: VideoEvidenceSummary
    visual_evidence: Optional[VisualEvidenceSummary] = None
    regulation_evidence: RegulationEvidenceSummary
    data_quality: DataQualityFlags
    provenance: Dict[str, EvidenceProvenanceRecord]

    # Decoupled evidence dimensions
    evidence_dimensions: EvidenceDimensions

    # Reference-lap baseline & evidence quantification
    baseline_evidence: Optional[BaselineEvidence] = None

    # Cornering overtake geometry & apex overlap analysis
    overtake_geometry: Optional[OvertakeGeometryEvidence] = None

    # Machine learning candidate evaluation (anomaly scoring without guilt/fault)
    ml_evidence: Optional[MLEvidence] = None

    steward_review_guide: str = Field(
        default="Review chronological timeline, minimum proximity frame, and relative braking inputs. "
        "Cross-reference camera angles when available and verify room afforded under FIA Driving Standards Guidelines."
    )


def synthesize_incident_evidence_dossier(
    candidate: CandidateDossier,
    raw_frames: List[TelemetryPointSchema],
    all_features: List[Any],
    session_rcm: Optional[List[Dict[str, Any]]] = None,
    video_source: Optional[VideoSourceMetadata] = None,
    baseline_evidence: Optional[BaselineEvidence] = None,
    overtake_geometry: Optional[OvertakeGeometryEvidence] = None,
    ml_evidence: Optional[MLEvidence] = None,
) -> IncidentEvidenceDossier:
    """Orchestrate the complete multi-modal evidence dossier synthesis."""
    dossier_id = f"DOSSIER-{candidate.candidate_id}"

    # 0a. Reference-Lap Baseline Synthesis (if not provided)
    if baseline_evidence is None and raw_frames:
        try:
            from app.services.baseline_service import get_baseline_service
            baseline_evidence = get_baseline_service().synthesize_baseline_evidence(
                candidate=candidate,
                raw_frames=raw_frames,
            )
        except Exception:
            baseline_evidence = None

    # 0b. Overtake Geometry & Apex Overlap Synthesis (if not provided)
    if overtake_geometry is None and raw_frames:
        try:
            from app.services.overtake_geometry_service import get_overtake_geometry_service
            overtake_geometry = get_overtake_geometry_service().synthesize_overtake_geometry(
                candidate=candidate,
                frames=raw_frames,
            )
        except Exception as e:
            overtake_geometry = None

    # 0c. ML Candidate Evaluation Synthesis (if not provided)
    if ml_evidence is None:
        try:
            features = extract_features_from_dossier_data(
                candidate=candidate,
                telemetry_frames=raw_frames,
                baseline_evidence=baseline_evidence,
                overtake_geometry=overtake_geometry,
            )
            ml_evidence = get_candidate_classifier().evaluate_candidate(
                incident_id=candidate.candidate_id,
                features=features,
            )
        except Exception:
            ml_evidence = None

    # 1. Telemetry Evidence Summary
    start_idx = 0
    peak_idx = len(raw_frames) // 2
    end_idx = len(raw_frames) - 1

    # Locate closest indices to candidate bounds if possible
    for i, f in enumerate(raw_frames):
        if f.timestamp == candidate.event_peak:
            peak_idx = i
            break

    tel_evidence = build_telemetry_evidence(
        driver_a=candidate.driver_a,
        driver_b=candidate.driver_b,
        raw_frames=raw_frames,
        start_index=start_idx,
        peak_index=peak_idx,
        end_index=end_idx,
        evidence_strength=candidate.evidence_strength,
    )

    # 2. Chronological Timeline
    peak_offset = raw_frames[peak_idx].time_offset if peak_idx < len(raw_frames) else 0.0
    timeline = generate_event_timeline(
        features=all_features,
        peak_offset=peak_offset,
        driver_a=candidate.driver_a,
        driver_b=candidate.driver_b,
    )

    # 3. Race Control Context
    rc_evidence = build_race_control_evidence(
        raw_messages=session_rcm or candidate.race_control_context,
        peak_timestamp_str=candidate.event_peak,
        driver_a=candidate.driver_a,
        driver_b=candidate.driver_b,
    )

    # 4. Video Evidence & Synchronization
    if video_source is not None:
        vid_evidence = build_video_evidence(
            session_id=candidate.session_id,
            event_start_str=candidate.event_start,
            event_peak_str=candidate.event_peak,
            event_end_str=candidate.event_end,
            source=video_source,
        )
    else:
        try:
            from app.services.video_service import get_video_service
            vid_evidence = get_video_service().build_video_evidence_for_candidate(
                candidate_id=candidate.candidate_id,
                session_id=candidate.session_id,
                event_start_str=candidate.event_start,
                event_peak_str=candidate.event_peak,
                event_end_str=candidate.event_end,
                selected_source=None,
            )
        except Exception:
            vid_evidence = build_video_evidence(
                session_id=candidate.session_id,
                event_start_str=candidate.event_start,
                event_peak_str=candidate.event_peak,
                event_end_str=candidate.event_end,
                source=None,
            )

    # 4.1 Visual Evidence & Multi-Modal Alignment (Prompt 13)
    try:
        from app.evidence.visual import get_visual_evidence_service
        vis_evidence = get_visual_evidence_service().build_visual_evidence_for_candidate(
            candidate_id=candidate.candidate_id,
            session_id=candidate.session_id,
            event_start_str=candidate.event_start,
            event_peak_str=candidate.event_peak,
            event_end_str=candidate.event_end,
            driver_a=candidate.driver_a,
            driver_b=candidate.driver_b,
            selected_source=video_source,
        )
    except Exception:
        vis_evidence = VisualEvidenceSummary(status=VisualObservationStatus.UNAVAILABLE)
    vid_evidence.visual_evidence = vis_evidence

    # 5. Regulatory Reference Linkages
    reg_evidence = match_relevant_regulations(
        event_type=candidate.event_type,
        minimum_gap=candidate.minimum_gap_meters,
        decel_delta_g=float(candidate.braking_change.get("decel_delta_g", 0.0)),
    )

    # 6. Provenance Tracking
    prov = build_default_provenance(session_id=candidate.session_id)

    # 7. Decoupled Evidence Dimensions
    dimensions = EvidenceDimensions(
        telemetry_evidence_strength=candidate.evidence_strength,
        race_control_context_strength=rc_evidence.race_control_context_strength,
        video_evidence_status=vid_evidence.video_evidence_status,
        regulation_reference_status=reg_evidence.status,
    )

    return IncidentEvidenceDossier(
        dossier_id=dossier_id,
        candidate_id=candidate.candidate_id,
        session_id=candidate.session_id,
        event_type=candidate.event_type,
        status=candidate.status,
        candidate=candidate,
        telemetry_evidence=tel_evidence,
        timeline=timeline,
        race_control_evidence=rc_evidence,
        video_evidence=vid_evidence,
        visual_evidence=vis_evidence,
        regulation_evidence=reg_evidence,
        data_quality=candidate.data_quality_flags,
        provenance=prov,
        evidence_dimensions=dimensions,
        baseline_evidence=baseline_evidence,
        overtake_geometry=overtake_geometry,
        ml_evidence=ml_evidence,
    )


def convert_dossier_to_frontend_incident(
    dossier: IncidentEvidenceDossier,
    circuit_name: str = "Monza",
    session_name: str = "Italian Grand Prix 2024 — Race",
) -> IncidentDetailResponse:
    """Transform an IncidentEvidenceDossier into the frontend IncidentDetailResponse contract."""
    cand = dossier.candidate
    tel = dossier.telemetry_evidence

    # Map timeline
    frontend_timeline = [
        IncidentTimelineMilestoneSchema(
            timestamp=m.timestamp,
            label=m.label,
            description=m.description,
            icon_type=m.icon_type,
            evidence_ref=m.evidence_ref,
        )
        for m in dossier.timeline
    ]

    # Map empirical evidence items
    evidence_items: List[EvidenceItemSchema] = [
        EvidenceItemSchema(
            id=f"EV-{cand.candidate_id}-01",
            category="PROXIMITY",
            title="Minimum Spatial Proximity",
            observed_value=f"{tel.minimum_gap_meters:.2f} meters",
            expected_context="Standard side-by-side wheel clearance is ~2.5m to 4.0m.",
            confidence=cand.evidence_strength,
            source="FastF1 3D Cartesian Coordinates (25Hz Resampled SI Grid)",
            description=f"Cars converged to {tel.minimum_gap_meters:.2f}m proximity at {cand.event_peak}.",
            verified=True,
        ),
        EvidenceItemSchema(
            id=f"EV-{cand.candidate_id}-02",
            category="RELATIVE_MOTION",
            title="Peak Approach Velocity",
            observed_value=f"{tel.peak_closing_speed_ms:.1f} m/s ({tel.peak_closing_speed_ms * 3.6:.0f} km/h)",
            expected_context="Typical corner entry closing rate is 0 to 10 m/s.",
            confidence=cand.evidence_strength,
            source="Central Finite Difference -d(gap)/dt",
            description=f"Relative approach rate peaked at {tel.peak_closing_speed_ms:.1f} m/s during corner entry.",
            verified=True,
        ),
    ]

    if tel.brake_delta_pct > 20.0:
        evidence_items.append(
            EvidenceItemSchema(
                id=f"EV-{cand.candidate_id}-03",
                category="VEHICLE_RESPONSE",
                title="Braking Differential",
                observed_value=f"{tel.driver_a} {tel.brake_a_pct:.0f}% vs {tel.driver_b} {tel.brake_b_pct:.0f}% (Delta {tel.brake_delta_pct:.0f}%)",
                expected_context="Synchronized braking delta is typically < 25%.",
                confidence=cand.evidence_strength,
                source="CAN-Bus Brake Pressure Feed",
                description=f"Significant braking disparity observed at apex moment.",
                verified=True,
            )
        )

    # Reference-Lap Baseline Quantification Evidence Items
    if dossier.baseline_evidence and dossier.baseline_evidence.status == BaselineStatus.AVAILABLE:
        for drv_code, drv_ev in dossier.baseline_evidence.drivers.items():
            if drv_ev.trajectory_metrics and drv_ev.trajectory_metrics.max_trajectory_deviation_m > 0.05:
                apex_str = f" (Apex: {drv_ev.trajectory_metrics.deviation_at_apex_m:.2f}m)" if drv_ev.trajectory_metrics.deviation_at_apex_m is not None else ""
                evidence_items.append(
                    EvidenceItemSchema(
                        id=f"EV-{cand.candidate_id}-TRAJ-{drv_code}",
                        category="TRAJECTORY",
                        title=f"{drv_code} Trajectory Line Deviation",
                        observed_value=f"Max: {drv_ev.trajectory_metrics.max_trajectory_deviation_m:.2f}m{apex_str}",
                        expected_context="Nominal reference lap line variance is typically < 0.35m.",
                        confidence=cand.evidence_strength,
                        source="Pointwise Median Reference-Lap Baseline (2D Cartesian Grid)",
                        description=f"{drv_code} deviated up to {drv_ev.trajectory_metrics.max_trajectory_deviation_m:.2f}m from clean reference racing line.",
                        verified=True,
                    )
                )
            if drv_ev.disruption_metrics and drv_ev.disruption_metrics.min_corner_speed_delta_kmh is not None:
                m = drv_ev.disruption_metrics
                evidence_items.append(
                    EvidenceItemSchema(
                        id=f"EV-{cand.candidate_id}-DISRUPT-{drv_code}",
                        category="VEHICLE_RESPONSE",
                        title=f"{drv_code} Apex Speed & Braking Disruption",
                        observed_value=f"Apex Speed: {m.speed_at_apex_incident_kmh:.0f} km/h (Delta {m.min_corner_speed_delta_kmh:+.1f} km/h), Braking Onset Delta {m.braking_onset_delta_m:+.1f}m",
                        expected_context="Nominal corner apex speed matches median reference within +/- 3 km/h.",
                        confidence=cand.evidence_strength,
                        source="Pointwise Median Reference-Lap Baseline",
                        description=f"{drv_code} experienced {m.min_corner_speed_delta_kmh:+.1f} km/h apex speed disparity vs clean reference laps.",
                        verified=True,
                    )
                )

    # Overtake Geometry Evidence Items
    if dossier.overtake_geometry:
        geom = dossier.overtake_geometry
        if geom.apex_snapshot and geom.apex_snapshot.overlap_percent is not None:
            evidence_items.append(
                EvidenceItemSchema(
                    id=f"EV-{cand.candidate_id}-GEOM-APEX",
                    category="GEOMETRY",
                    title="Apex Overlap & Proximity",
                    observed_value=f"{geom.apex_snapshot.overlap_percent:.1f}% ({geom.overlap_classification.value})",
                    expected_context="FIA Guidelines reference: >=50% overlap (front axle alongside mirror/front axle) at apex.",
                    confidence=cand.evidence_strength,
                    source="FastF1 Resampled Trajectory & Vehicle Dimension Reference (5.63m)",
                    description=f"{geom.driver_incident} reached {geom.apex_snapshot.overlap_percent:.1f}% longitudinal overlap relative to {geom.driver_other} at corner apex.",
                    verified=True,
                )
            )
        if geom.exit_clearance and geom.exit_clearance.measured_clearance_m is not None:
            clearance_val = geom.exit_clearance.measured_clearance_m
            evidence_items.append(
                EvidenceItemSchema(
                    id=f"EV-{cand.candidate_id}-GEOM-EXIT",
                    category="GEOMETRY",
                    title="Corner Exit Lateral Clearance",
                    observed_value=f"{clearance_val:.2f}m vs 2.00m reference ({geom.exit_clearance.clearance_classification.value})",
                    expected_context="Modern F1 regulation vehicle reference width is 2.00m.",
                    confidence=cand.evidence_strength,
                    source="FastF1 GPS Spatial Coordinates at Throttle Reapplication Exit",
                    description=f"Measured lateral clearance at corner exit was {clearance_val:.2f}m compared to 2.00m reference width.",
                    verified=True,
                )
            )

    # Visual Evidence Items (Prompt 13)
    if dossier.visual_evidence and dossier.visual_evidence.status == VisualObservationStatus.OBSERVED:
        vis = dossier.visual_evidence
        align_str = vis.cross_modal_alignment.alignment_status.value if vis.cross_modal_alignment else "UNVERIFIED"
        delta_str = f" ({vis.cross_modal_alignment.delta_seconds:+.2f}s)" if vis.cross_modal_alignment and vis.cross_modal_alignment.delta_seconds is not None else ""
        evidence_items.append(
            EvidenceItemSchema(
                id=f"EV-{cand.candidate_id}-VIS-01",
                category="VISUAL",
                title="Image-Plane Proximity & Alignment",
                observed_value=f"Cross-Modal Status: {align_str}{delta_str}",
                expected_context="Visual closest proximity frame correlates with telemetry peak within +/-0.20s tolerance.",
                confidence=cand.evidence_strength,
                source=f"Calibrated Camera Analysis ({vis.camera_label or 'Camera'})",
                description=f"Bounded visual tracking evaluated across {len(vis.keyframes)} keyframes with 2D perspective projection.",
                verified=True,
            )
        )

    # Map regulations
    frontend_regs = [
        RelevantRegulationSchema(
            id=r.id,
            document=r.document,
            article=r.article,
            title=r.title,
            regulation_text_placeholder=r.text_reference,
            why_relevant=r.relevance_reason,
            match_reason="Algorithmic match based on empirical interaction kinematics.",
            relevance=r.relevance_level,
            source=r.series,
            source_url=r.source_url,
        )
        for r in dossier.regulation_evidence.references
    ]

    # Map connections
    frontend_connections = [
        EvidenceRegulationConnectionSchema(
            observed_evidence=link.observed_evidence,
            relevant_regulation=link.relevant_regulation,
            steward_review_action=link.steward_review_action,
        )
        for link in dossier.regulation_evidence.evidence_links
    ]

    # Video availability
    vid_avail = dossier.video_evidence.video_evidence_status in (
        VideoSyncStatus.VIDEO_AVAILABLE,
        VideoSyncStatus.VIDEO_SYNCHRONIZED,
    )
    vid_path = None
    if vid_avail and dossier.video_evidence.sources:
        vid_path = dossier.video_evidence.sources[0].source_url

    uncertainties: List[str] = []
    if dossier.video_evidence.video_evidence_status == VideoSyncStatus.VIDEO_UNAVAILABLE:
        uncertainties.append("Broadcast video footage is unlinked/unavailable. Analysis is based strictly on telemetry and race control records.")
    if not tel.same_lap:
        uncertainties.append("Drivers are on different official lap numbers (blue flag or unlapping condition).")

    sources = EvidenceSources(
        telemetry="FastF1 ECU CAN-Bus + GPS 25Hz SI Grid",
        video=f"Status: {dossier.video_evidence.video_evidence_status.value}",
        regulations="FIA Formula One Sporting Regulations 2024 & ISC Appendix L",
    )

    return IncidentDetailResponse(
        id=cand.candidate_id,
        session=session_name,
        race_id=cand.session_id,
        circuit=circuit_name,
        lap=cand.lap_number_a or 1,
        turn=cand.turn or "Track Sector",
        timestamp=cand.event_peak,
        time_window=TimeWindow(start=cand.event_start, end=cand.event_end),
        driver_a=cand.driver_a,
        driver_b=cand.driver_b,
        incident_type=cand.event_type.value,
        confidence=cand.evidence_strength,
        status="REQUIRES_REVIEW",
        severity="HIGH" if cand.event_type == CandidateEventType.CONTACT_CANDIDATE else "MEDIUM",
        summary=cand.summary,
        detection_method=cand.detection_method,
        video_available=vid_avail,
        video_path=vid_path,
        telemetry_available=True,
        regulations_available=len(frontend_regs) > 0,
        sources=sources,
        evidence_assessment=evidence_items,
        relevant_regulations=frontend_regs,
        evidence_connections=frontend_connections,
        timeline=frontend_timeline,
        uncertainties=uncertainties,
        baseline_evidence=dossier.baseline_evidence,
        overtake_geometry=dossier.overtake_geometry,
        ml_evidence=dossier.ml_evidence,
        video_evidence=dossier.video_evidence,
        visual_evidence=dossier.visual_evidence,
    )
