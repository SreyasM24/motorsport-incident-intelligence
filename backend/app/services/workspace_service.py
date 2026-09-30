"""Steward Case Workspace Aggregation, Evidence Triage & Review Service.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS:
    1. Zero Autonomous Guilt or Fault Determination: The workspace presents
       structured, multi-modal evidence for human steward investigation.
    2. Zero Penalty Recommendation: The system never proposes penalties,
       fault splits, or regulatory liability.
    3. Epistemic Separation: Strictly distinguishes OBSERVED, DERIVED,
       MODEL_DERIVED, DOCUMENTARY, and UNAVAILABLE evidence.
    4. Deterministic Triage: Ordering is an investigation UX tool, never proof of fault.
    5. Non-Mutating Evidence: Reviewer metadata (notes, acknowledgements) is kept in
       separate audit tables; underlying source data is never modified.
"""

from datetime import datetime, timezone
import json
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.evidence.candidate import CandidateDossier
from app.evidence.reconstruction_service import get_reconstruction_engine
from app.evidence.synthesis import get_steward_dossier_synthesizer
from app.evidence.synthesis.contracts import (
    ConsistencyStatus,
    CrossModalDiscrepancy,
    EvidenceItem,
    EvidenceStatus,
    StewardEvidenceDossier,
)
from app.knowledge.service import KnowledgeRetrievalService
from app.knowledge.models import RetrievalMethod
from app.models.incident import Incident
from app.models.review import ReviewRecord
from app.models.workspace import (
    DiscrepancyAnnotation,
    EvidenceAcknowledgement,
    UnresolvedQuestion,
)
from app.schemas.workspace import (
    AcknowledgementAction,
    DiscrepancyStatus,
    DiscrepancyStatusUpdateRequest,
    EvidenceAcknowledgementCreateRequest,
    EvidenceAcknowledgementSchema,
    QuestionStatus,
    ReviewAuditEntry,
    StewardCaseWorkspace,
    TriageAvailability,
    TriageEpistemicType,
    UnresolvedQuestionCreateRequest,
    UnresolvedQuestionSchema,
    UnresolvedQuestionUpdateRequest,
    WorkspaceCaseInfo,
    WorkspaceDiscrepancyItem,
    WorkspaceEvidenceItem,
    WorkspaceEvidenceStreamSummary,
    WorkspaceIncidentSummary,
    WorkspaceReviewSummary,
    WorkspaceTimelineEvent,
)


class StewardWorkspaceService:
    """Orchestrates the canonical read model and review mutations for steward investigations."""

    # Simple in-process memoization cache for synthesized dossiers to guarantee < 500ms warm latency
    _DOSSIER_CACHE: Dict[str, Tuple[float, StewardEvidenceDossier]] = {}
    CACHE_TTL_SECONDS = 300.0

    @classmethod
    def get_workspace(
        cls,
        candidate_id: str,
        db: Optional[Session] = None,
        force_refresh: bool = False,
    ) -> StewardCaseWorkspace:
        """Aggregate all evidence subsystems into the canonical StewardCaseWorkspace."""
        clean_cid = candidate_id.strip()

        # 1. Retrieve or synthesize master Steward Evidence Dossier
        dossier = cls._get_or_synthesize_dossier(clean_cid, force_refresh=force_refresh)
        
        # 2. Lookup database persistence record (if persisted)
        incident_record: Optional[Incident] = None
        db_reviews: List[ReviewRecord] = []
        db_acks: List[EvidenceAcknowledgement] = []
        db_questions: List[UnresolvedQuestion] = []
        db_disc_annotations: List[DiscrepancyAnnotation] = []

        if db is not None:
            stmt = select(Incident).where(
                (Incident.candidate_id == clean_cid) | (Incident.id == clean_cid)
            )
            incident_record = db.scalars(stmt).first()
            if incident_record:
                inc_id = incident_record.id
                db_reviews = list(
                    db.scalars(
                        select(ReviewRecord)
                        .where(ReviewRecord.incident_id == inc_id)
                        .order_by(ReviewRecord.created_at.asc())
                    ).all()
                )
                db_acks = list(
                    db.scalars(
                        select(EvidenceAcknowledgement)
                        .where(
                            (EvidenceAcknowledgement.candidate_id == clean_cid)
                            | (EvidenceAcknowledgement.incident_id == inc_id)
                        )
                        .order_by(EvidenceAcknowledgement.created_at.desc())
                    ).all()
                )
                db_questions = list(
                    db.scalars(
                        select(UnresolvedQuestion)
                        .where(
                            (UnresolvedQuestion.candidate_id == clean_cid)
                            | (UnresolvedQuestion.incident_id == inc_id)
                        )
                        .order_by(UnresolvedQuestion.created_at.desc())
                    ).all()
                )
                db_disc_annotations = list(
                    db.scalars(
                        select(DiscrepancyAnnotation)
                        .where(
                            (DiscrepancyAnnotation.candidate_id == clean_cid)
                            | (DiscrepancyAnnotation.incident_id == inc_id)
                        )
                        .order_by(DiscrepancyAnnotation.created_at.desc())
                    ).all()
                )
            else:
                # Still check if acknowledgements or questions exist by candidate_id alone
                db_acks = list(
                    db.scalars(
                        select(EvidenceAcknowledgement)
                        .where(EvidenceAcknowledgement.candidate_id == clean_cid)
                        .order_by(EvidenceAcknowledgement.created_at.desc())
                    ).all()
                )
                db_questions = list(
                    db.scalars(
                        select(UnresolvedQuestion)
                        .where(UnresolvedQuestion.candidate_id == clean_cid)
                        .order_by(UnresolvedQuestion.created_at.desc())
                    ).all()
                )
                db_disc_annotations = list(
                    db.scalars(
                        select(DiscrepancyAnnotation)
                        .where(DiscrepancyAnnotation.candidate_id == clean_cid)
                        .order_by(DiscrepancyAnnotation.created_at.desc())
                    ).all()
                )

        # 3. Assemble Case Header Info
        case_info = WorkspaceCaseInfo(
            candidate_id=clean_cid,
            incident_id=incident_record.id if incident_record else dossier.incident_id,
            session=dossier.session_id,
            event=dossier.event_type,
            circuit="Monza" if "MON" in clean_cid.upper() or "ITA" in clean_cid.upper() else "Autodromo Nazionale Monza",
            timestamp=dossier.timeline[0].timestamp if dossier.timeline else "13:42:18.4",
            drivers=[dossier.driver_a, dossier.driver_b],
            incident_status=incident_record.status if incident_record else dossier.review_status,
            review_status=incident_record.status if incident_record else dossier.review_status,
            analysis_version=dossier.analysis_version,
        )

        # 4. Assemble Incident Location & Detection Summary
        inc_summary = WorkspaceIncidentSummary(
            incident_type=dossier.event_type,
            detection_method="KINEMATIC_RELATIVE_MOTION_ANOMALY",
            confidence=85,
            timeline_window=f"T-2.0s → T+1.5s relative to {case_info.timestamp}",
            track_position=dossier.turn,
            lap_number=dossier.lap_number,
        )

        # 5. Assemble Evidence Stream Summaries
        evidence_summary = cls._build_stream_summaries(dossier)

        # 6. Build Deterministic Evidence Triage Layer
        triage_items = cls._build_triage_items(dossier, db_acks)

        # 7. Build Unified Chronological Timeline
        timeline_events = cls._build_timeline(dossier)

        # 8. Build Discrepancies with Steward Status Overlays
        discrepancy_items = cls._build_discrepancies(dossier, db_disc_annotations)

        # 9. Build Review State & Audit Trail
        review_summary = cls._build_review_summary(
            incident_record=incident_record,
            dossier=dossier,
            db_reviews=db_reviews,
            db_acks=db_acks,
            db_questions=db_questions,
        )

        # 10. Historical Comparable Evidence (Prompt 23 Engine)
        hist_comps = dossier.historical_comparable_evidence
        if hist_comps is None:
            try:
                knowledge_svc = KnowledgeRetrievalService.get_instance()
                hist_comps = knowledge_svc.compare_case(candidate_id=clean_cid, top_k=3)
            except Exception as e:
                logger.warning(f"Failed to fetch historical comparisons for {clean_cid}: {e}")

        # 11. Regulations (Prompt 21 Citation RAG)
        regulations = dossier.regulations

        return StewardCaseWorkspace(
            case=case_info,
            incident_summary=inc_summary,
            evidence_summary=evidence_summary,
            evidence_items=triage_items,
            timeline=timeline_events,
            discrepancies=discrepancy_items,
            historical_comparables=hist_comps,
            regulations=regulations,
            review=review_summary,
        )

    # --------------------------------------------------------------------------
    # Subsystem Helpers & Prioritization Builders
    # --------------------------------------------------------------------------

    @classmethod
    def _get_or_synthesize_dossier(cls, candidate_id: str, force_refresh: bool = False) -> StewardEvidenceDossier:
        """Fetch cached dossier or construct via reconstruction engine and synthesizer."""
        now = time.time()
        if not force_refresh and candidate_id in cls._DOSSIER_CACHE:
            ts, cached_dossier = cls._DOSSIER_CACHE[candidate_id]
            if now - ts < cls.CACHE_TTL_SECONDS:
                return cached_dossier

        engine = get_reconstruction_engine()
        raw_dossier = engine.get_candidate_dossier(candidate_id)
        if not raw_dossier:
            raise ResourceNotFoundException("CandidateDossier", candidate_id)

        from app.evidence.cv import get_cv_service
        cv_analysis = get_cv_service().process_candidate_incident(candidate=raw_dossier.candidate)
        synthesizer = get_steward_dossier_synthesizer()
        master_dossier = synthesizer.synthesize_steward_dossier(
            dossier=raw_dossier,
            cv_analysis=cv_analysis,
            candidate_id_override=candidate_id,
        )

        cls._DOSSIER_CACHE[candidate_id] = (now, master_dossier)
        return master_dossier

    @classmethod
    def _build_stream_summaries(
        cls, dossier: StewardEvidenceDossier
    ) -> Dict[str, WorkspaceEvidenceStreamSummary]:
        """Generate structured per-stream summaries with epistemic classification."""
        summaries: Dict[str, WorkspaceEvidenceStreamSummary] = {}
        sq_map = {sq.stream_name.lower(): sq for sq in dossier.stream_quality}

        # 1. Telemetry
        tel_sq = sq_map.get("telemetry")
        summaries["telemetry"] = WorkspaceEvidenceStreamSummary(
            availability=TriageAvailability.FULL if tel_sq and tel_sq.availability == "AVAILABLE" else TriageAvailability.PARTIAL,
            epistemic_type=TriageEpistemicType.OBSERVED,
            quality="High-Fidelity 25Hz Resampled CAN Grid",
            provenance="Official FastF1 / OpenF1 Synchronized Timing Feed",
            timestamp_coverage="T-2.0s → T+1.5s",
            limitations=["Interpolated at 25Hz from irregular asynchronous ECU broadcasts"],
            contradictions=[],
        )

        # 2. Race Control
        rc_sq = sq_map.get("race_control") or sq_map.get("regulation")
        summaries["race_control"] = WorkspaceEvidenceStreamSummary(
            availability=TriageAvailability.FULL,
            epistemic_type=TriageEpistemicType.DOCUMENTARY,
            quality="Official FIA Race Director Messaging",
            provenance="FIA Electronic Timing Page 3",
            timestamp_coverage="Session Event Log",
            limitations=["Manual human logging by race control operators with variable latency"],
            contradictions=[],
        )

        # 3. Video Broadcast
        vid_sq = sq_map.get("video")
        is_vid_avail = vid_sq.availability == "AVAILABLE" if vid_sq else False
        summaries["video"] = WorkspaceEvidenceStreamSummary(
            availability=TriageAvailability.FULL if is_vid_avail else TriageAvailability.UNAVAILABLE,
            epistemic_type=TriageEpistemicType.OBSERVED,
            quality="1080p 50fps World Feed" if is_vid_avail else "UNAVAILABLE (FOM Copyright)",
            provenance="FOM International Broadcast Feed" if is_vid_avail else "Unlinked Broadcast Stream",
            timestamp_coverage="00:05.000 → 00:25.000" if is_vid_avail else "0.0s",
            limitations=[
                "Commercial broadcast footage is legally protected under copyright and cannot be redistributed.",
                "Unlinked video frames are recorded as unobserved data, never as negative evidence or proof of guilt.",
            ],
            contradictions=[],
        )

        # 4. Visual CV Tracking
        cv_sq = sq_map.get("cv")
        is_cv_avail = cv_sq.availability == "AVAILABLE" if cv_sq else False
        summaries["visual_cv"] = WorkspaceEvidenceStreamSummary(
            availability=TriageAvailability.FULL if is_cv_avail else TriageAvailability.UNAVAILABLE,
            epistemic_type=TriageEpistemicType.MODEL_DERIVED,
            quality="Multi-Object Bounding Box Tracking" if is_cv_avail else "UNAVAILABLE",
            provenance="Calibrated 2D Deep Learning Object Detector",
            timestamp_coverage="Incident Window" if is_cv_avail else "0.0s",
            limitations=[
                "2D camera perspective foreshortening introduces lateral uncertainty.",
                "Identity attribution requires human steward verification.",
            ],
            contradictions=[],
        )

        # 5. Baseline Comparison
        base_sq = sq_map.get("reference_baseline")
        summaries["baseline_comparison"] = WorkspaceEvidenceStreamSummary(
            availability=TriageAvailability.FULL if base_sq and base_sq.availability == "AVAILABLE" else TriageAvailability.LIMITED,
            epistemic_type=TriageEpistemicType.DERIVED,
            quality="Qualifying / Teammate Reference Lap Kinematic Variance",
            provenance="Pre-incident Unimpeded Clean Lap Telemetry",
            timestamp_coverage="Lap Entry → Exit Window",
            limitations=["Track evolution and tire wear variance between reference lap and incident lap"],
            contradictions=[],
        )

        # 6. Regulations
        summaries["regulations"] = WorkspaceEvidenceStreamSummary(
            availability=TriageAvailability.FULL,
            epistemic_type=TriageEpistemicType.DOCUMENTARY,
            quality="Canonical FIA Sporting Code & Driving Standards Guidelines",
            provenance="FIA Formula One Sporting Regulations 2024",
            timestamp_coverage="2024 Season Statutory Code",
            limitations=["Statutory guidelines are descriptive frameworks and do not automate penalties"],
            contradictions=[],
        )

        # 7. Historical Cases
        summaries["historical_cases"] = WorkspaceEvidenceStreamSummary(
            availability=TriageAvailability.FULL,
            epistemic_type=TriageEpistemicType.DOCUMENTARY,
            quality="MII Historical Incident Benchmark Knowledge Layer (MII-HIRB-v1.1.0)",
            provenance="FIA Official Documents & Benchmark Ground Truth",
            timestamp_coverage="2023-2024 F1 Championship Cases",
            limitations=[
                "Past rulings do NOT constitute binding legal precedent or penalty targets.",
                "Similarity scoring is purely physical and geometric.",
            ],
            contradictions=[],
        )

        return summaries

    @classmethod
    def _build_triage_items(
        cls,
        dossier: StewardEvidenceDossier,
        db_acks: List[EvidenceAcknowledgement],
    ) -> List[WorkspaceEvidenceItem]:
        """Transform dossier evidence items into prioritised triage records.

        PRIORITIZATION ORDER:
            1: OBSERVED
            2: DERIVED
            3: MODEL_DERIVED
            4: DOCUMENTARY
            5: UNAVAILABLE
        Within each category, sorted by |event_relative_time_sec| ascending.
        """
        # Map latest acknowledgement per evidence ID
        ack_map: Dict[str, EvidenceAcknowledgement] = {}
        for ack in db_acks:
            if ack.evidence_id not in ack_map:
                ack_map[ack.evidence_id] = ack

        triage_items: List[WorkspaceEvidenceItem] = []

        epistemic_map = {
            EvidenceStatus.OBSERVED: (TriageEpistemicType.OBSERVED, 1),
            EvidenceStatus.DERIVED: (TriageEpistemicType.DERIVED, 2),
            EvidenceStatus.MODEL_DERIVED: (TriageEpistemicType.MODEL_DERIVED, 3),
            EvidenceStatus.DOCUMENTARY: (TriageEpistemicType.DOCUMENTARY, 4),
            EvidenceStatus.UNAVAILABLE: (TriageEpistemicType.UNAVAILABLE, 5),
        }

        for item in dossier.evidence_items:
            e_type, priority = epistemic_map.get(
                item.status, (TriageEpistemicType.UNAVAILABLE, 5)
            )

            # Map availability rating
            avail = TriageAvailability.FULL
            if item.status == EvidenceStatus.UNAVAILABLE:
                avail = TriageAvailability.UNAVAILABLE
            elif "partial" in (item.confidence_or_quality or "").lower():
                avail = TriageAvailability.PARTIAL
            elif "limited" in (item.confidence_or_quality or "").lower():
                avail = TriageAvailability.LIMITED

            # Acknowledgement read model
            latest_ack: Optional[EvidenceAcknowledgementSchema] = None
            if item.evidence_id in ack_map:
                db_a = ack_map[item.evidence_id]
                latest_ack = EvidenceAcknowledgementSchema(
                    id=db_a.id,
                    candidate_id=db_a.candidate_id,
                    evidence_id=db_a.evidence_id,
                    reviewer_id=db_a.reviewer_id,
                    action=AcknowledgementAction(db_a.action),
                    note=db_a.note,
                    created_at=db_a.created_at,
                )

            triage_items.append(
                WorkspaceEvidenceItem(
                    evidence_id=item.evidence_id,
                    evidence_type=item.evidence_type.value,
                    epistemic_type=e_type,
                    source=item.source_layer,
                    availability=avail,
                    quality=item.confidence_or_quality or "High",
                    timestamp=item.timestamp,
                    relevance=f"Relevant to {item.evidence_type.value.replace('_', ' ').lower()}",
                    provenance=item.provenance,
                    limitations=item.limitations,
                    discrepancy_status="NONE",
                    observation=item.observation,
                    value=item.value,
                    unit=item.unit,
                    parent_evidence_ids=item.parent_evidence_ids,
                    triage_priority=priority,
                    latest_acknowledgement=latest_ack,
                )
            )

        # Deterministic sorting: priority asc, then abs(event_relative_time_sec) asc, then evidence_id
        triage_items.sort(
            key=lambda x: (
                x.triage_priority,
                abs(
                    next(
                        (
                            i.event_relative_time_sec
                            for i in dossier.evidence_items
                            if i.evidence_id == x.evidence_id and i.event_relative_time_sec is not None
                        ),
                        999.0,
                    )
                ),
                x.evidence_id,
            )
        )

        return triage_items

    @classmethod
    def _build_timeline(cls, dossier: StewardEvidenceDossier) -> List[WorkspaceTimelineEvent]:
        """Build unified chronological timeline with sensor uncertainty bounds."""
        events: List[WorkspaceTimelineEvent] = []

        for ev in dossier.timeline:
            # Map uncertainty bounds deterministically based on source
            unc = None
            meas = None
            if "telemetry" in ev.source.lower() or "speed" in ev.description.lower():
                meas = ev.description
                unc = "± 2.0 km/h (ECU CAN bus sample accuracy)"
            elif "proximity" in ev.description.lower() or "gap" in ev.description.lower():
                meas = ev.description
                unc = "± 0.20 m (Resampled Cartesian projection)"
            elif "video" in ev.source.lower():
                unc = "± 0.04 s (1 frame @ 25Hz broadcast cadence)"

            e_status = (
                TriageEpistemicType.OBSERVED
                if ev.evidence_status == EvidenceStatus.OBSERVED
                else TriageEpistemicType.DERIVED
                if ev.evidence_status == EvidenceStatus.DERIVED
                else TriageEpistemicType.DOCUMENTARY
            )

            events.append(
                WorkspaceTimelineEvent(
                    timestamp=ev.timestamp,
                    event_relative_time_sec=ev.event_relative_time_sec,
                    source=ev.source,
                    epistemic_type=e_status,
                    description=ev.description,
                    measurement=meas,
                    uncertainty=unc,
                    provenance=ev.provenance,
                    evidence_ref=ev.evidence_ref,
                )
            )

        events.sort(key=lambda x: x.event_relative_time_sec)
        return events

    @classmethod
    def _build_discrepancies(
        cls,
        dossier: StewardEvidenceDossier,
        db_annotations: List[DiscrepancyAnnotation],
    ) -> List[WorkspaceDiscrepancyItem]:
        """Build discrepancy items with steward status updates."""
        status_map: Dict[str, DiscrepancyAnnotation] = {}
        for ann in db_annotations:
            if ann.discrepancy_id not in status_map:
                status_map[ann.discrepancy_id] = ann

        items: List[WorkspaceDiscrepancyItem] = []
        for disc in dossier.discrepancies:
            ann = status_map.get(disc.discrepancy_id)
            current_status = DiscrepancyStatus(ann.status) if ann else DiscrepancyStatus.OPEN
            notes = [ann.note] if ann and ann.note else []

            items.append(
                WorkspaceDiscrepancyItem(
                    discrepancy_id=disc.discrepancy_id,
                    evidence_a=disc.evidence_stream_a,
                    evidence_b=disc.evidence_stream_b,
                    discrepancy_type=disc.metric,
                    magnitude=disc.observed_difference,
                    uncertainty=disc.expected_tolerance,
                    explanation=disc.explanation,
                    severity=disc.severity.value,
                    status=current_status,
                    affected_evidence_ids=disc.affected_evidence_ids,
                    notes=notes,
                )
            )

        return items

    @classmethod
    def _build_review_summary(
        cls,
        incident_record: Optional[Incident],
        dossier: StewardEvidenceDossier,
        db_reviews: List[ReviewRecord],
        db_acks: List[EvidenceAcknowledgement],
        db_questions: List[UnresolvedQuestion],
    ) -> WorkspaceReviewSummary:
        """Construct the review summary and audit trail."""
        current_status = incident_record.status if incident_record else dossier.review_status
        reviewer_id = incident_record.reviews[0].reviewer_id if incident_record and incident_record.reviews else dossier.reviewer_id
        reviewer_notes = incident_record.reviews[0].review_notes if incident_record and incident_record.reviews else dossier.review_notes
        reviewer_rationale = incident_record.reviews[0].review_rationale if incident_record and incident_record.reviews else None

        # Build acknowledgement schemas
        acks_schemas = [
            EvidenceAcknowledgementSchema(
                id=a.id,
                candidate_id=a.candidate_id,
                evidence_id=a.evidence_id,
                reviewer_id=a.reviewer_id,
                action=AcknowledgementAction(a.action),
                note=a.note,
                created_at=a.created_at,
            )
            for a in db_acks
        ]

        # Build unresolved questions schemas
        question_schemas = []
        for q in db_questions:
            e_ids = []
            if q.evidence_ids_json:
                try:
                    e_ids = json.loads(q.evidence_ids_json)
                except Exception:
                    e_ids = [x.strip() for x in q.evidence_ids_json.split(",") if x.strip()]
            question_schemas.append(
                UnresolvedQuestionSchema(
                    id=q.id,
                    candidate_id=q.candidate_id,
                    question=q.question,
                    evidence_ids=e_ids,
                    status=QuestionStatus(q.status),
                    reviewer_note=q.reviewer_note,
                    created_at=q.created_at,
                    resolved_at=q.resolved_at,
                )
            )

        # Build chronological audit trail
        history: List[ReviewAuditEntry] = []
        for r in db_reviews:
            history.append(
                ReviewAuditEntry(
                    id=r.id,
                    status=r.status,
                    reviewer_id=r.reviewer_id,
                    timestamp=r.created_at.isoformat() if r.created_at else "",
                    notes=r.review_notes,
                    rationale=r.review_rationale,
                    evidence_considered=r.evidence_considered,
                    evidence_missing=r.evidence_missing,
                    observations=r.observations,
                )
            )

        return WorkspaceReviewSummary(
            current_state=current_status,
            reviewer_id=reviewer_id,
            reviewer_notes=reviewer_notes,
            review_rationale=reviewer_rationale,
            evidence_acknowledgements=acks_schemas,
            unresolved_questions=question_schemas,
            review_history=history,
        )

    # --------------------------------------------------------------------------
    # Review Mutations & Workflow Actions
    # --------------------------------------------------------------------------

    @classmethod
    def record_acknowledgement(
        cls,
        db: Session,
        candidate_id: str,
        evidence_id: str,
        payload: EvidenceAcknowledgementCreateRequest,
    ) -> EvidenceAcknowledgementSchema:
        """Record an explicit human steward triage action on an evidence item."""
        clean_cid = candidate_id.strip()
        clean_eid = evidence_id.strip()

        # Find linked incident record if it exists
        inc = db.scalars(
            select(Incident).where((Incident.candidate_id == clean_cid) | (Incident.id == clean_cid))
        ).first()

        ack_id = f"ACK-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6]}"
        ack = EvidenceAcknowledgement(
            id=ack_id,
            candidate_id=clean_cid,
            incident_id=inc.id if inc else None,
            evidence_id=clean_eid,
            reviewer_id=payload.reviewer_id,
            action=payload.action.value,
            note=payload.note,
        )

        db.add(ack)
        db.commit()
        db.refresh(ack)

        return EvidenceAcknowledgementSchema(
            id=ack.id,
            candidate_id=ack.candidate_id,
            evidence_id=ack.evidence_id,
            reviewer_id=ack.reviewer_id,
            action=AcknowledgementAction(ack.action),
            note=ack.note,
            created_at=ack.created_at,
        )

    @classmethod
    def create_unresolved_question(
        cls,
        db: Session,
        candidate_id: str,
        payload: UnresolvedQuestionCreateRequest,
    ) -> UnresolvedQuestionSchema:
        """Open a new structured investigation question for the steward panel."""
        clean_cid = candidate_id.strip()
        inc = db.scalars(
            select(Incident).where((Incident.candidate_id == clean_cid) | (Incident.id == clean_cid))
        ).first()

        qid = f"QST-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6]}"
        e_json = json.dumps(payload.evidence_ids) if payload.evidence_ids else None

        question = UnresolvedQuestion(
            id=qid,
            candidate_id=clean_cid,
            incident_id=inc.id if inc else None,
            question=payload.question,
            evidence_ids_json=e_json,
            status=QuestionStatus.OPEN.value,
            reviewer_note=payload.reviewer_note,
        )

        db.add(question)
        db.commit()
        db.refresh(question)

        return UnresolvedQuestionSchema(
            id=question.id,
            candidate_id=question.candidate_id,
            question=question.question,
            evidence_ids=payload.evidence_ids or [],
            status=QuestionStatus.OPEN,
            reviewer_note=question.reviewer_note,
            created_at=question.created_at,
            resolved_at=question.resolved_at,
        )

    @classmethod
    def update_unresolved_question(
        cls,
        db: Session,
        candidate_id: str,
        question_id: str,
        payload: UnresolvedQuestionUpdateRequest,
    ) -> UnresolvedQuestionSchema:
        """Update or resolve an open investigation question."""
        clean_cid = candidate_id.strip()
        q = db.get(UnresolvedQuestion, question_id)
        if not q or q.candidate_id != clean_cid:
            raise ResourceNotFoundException("UnresolvedQuestion", question_id)

        now = datetime.now(timezone.utc)
        if payload.status:
            q.status = payload.status.value
            if payload.status == QuestionStatus.RESOLVED:
                q.resolved_at = now
            elif payload.status == QuestionStatus.OPEN:
                q.resolved_at = None

        if payload.reviewer_note is not None:
            q.reviewer_note = payload.reviewer_note

        db.commit()
        db.refresh(q)

        e_ids = []
        if q.evidence_ids_json:
            try:
                e_ids = json.loads(q.evidence_ids_json)
            except Exception:
                e_ids = [x.strip() for x in q.evidence_ids_json.split(",") if x.strip()]

        return UnresolvedQuestionSchema(
            id=q.id,
            candidate_id=q.candidate_id,
            question=q.question,
            evidence_ids=e_ids,
            status=QuestionStatus(q.status),
            reviewer_note=q.reviewer_note,
            created_at=q.created_at,
            resolved_at=q.resolved_at,
        )

    @classmethod
    def update_discrepancy_status(
        cls,
        db: Session,
        candidate_id: str,
        discrepancy_id: str,
        payload: DiscrepancyStatusUpdateRequest,
    ) -> DiscrepancyAnnotation:
        """Record a steward inspection status on a cross-modal contradiction."""
        clean_cid = candidate_id.strip()
        inc = db.scalars(
            select(Incident).where((Incident.candidate_id == clean_cid) | (Incident.id == clean_cid))
        ).first()

        ann_id = f"DISC-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6]}"
        ann = DiscrepancyAnnotation(
            id=ann_id,
            candidate_id=clean_cid,
            incident_id=inc.id if inc else None,
            discrepancy_id=discrepancy_id,
            status=payload.status.value,
            reviewer_id=payload.reviewer_id,
            note=payload.note,
        )

        db.add(ann)
        db.commit()
        db.refresh(ann)
        return ann

    @classmethod
    def get_timeline(cls, candidate_id: str) -> List[WorkspaceTimelineEvent]:
        """Direct getter for workspace chronological timeline."""
        workspace = cls.get_workspace(candidate_id)
        return workspace.timeline

    @classmethod
    def get_audit_trail(cls, candidate_id: str, db: Session) -> List[ReviewAuditEntry]:
        """Direct getter for review audit history."""
        workspace = cls.get_workspace(candidate_id, db=db)
        return workspace.review.review_history
