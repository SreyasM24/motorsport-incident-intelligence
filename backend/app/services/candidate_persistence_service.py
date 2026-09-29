"""Service for idempotent candidate persistence and human steward review state transitions.

CRITICAL JURISPRUDENTIAL DOCTRINE:
    This service manages decision-support records for human race stewards.
    It NEVER automates guilt, fault, liability, or sporting penalties.
"""

from datetime import datetime, timezone
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.core.logging import logger
from app.evidence.candidate import CandidateDossier, CandidateEventType
from app.evidence.reconstruction_service import get_reconstruction_engine
from app.models.driver import Driver
from app.models.incident import Incident
from app.models.incident_driver import IncidentDriver
from app.models.race import Race
from app.models.review import ReviewRecord
from app.models.session import Session as DBSession
from app.schemas.review import (
    BulkCandidatePersistRequest,
    BulkCandidatePersistResponse,
    CandidatePersistResponse,
    ReviewCreateRequest,
    ReviewRecordSchema,
    ReviewStatus,
)


# ==============================================================================
# 1. State Machine Definitions & Transition Validation
# ==============================================================================

# Allowed standard transitions between lifecycle states
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "REQUIRES_REVIEW": ["UNDER_REVIEW"],
    "UNDER_REVIEW": ["REVIEWED", "DISMISSED", "REQUIRES_REVIEW"],
    "REVIEWED": ["UNDER_REVIEW"],  # Allowed only via explicit reopening
    "DISMISSED": ["UNDER_REVIEW"],  # Allowed only via explicit reopening
    "DETECTED": ["REQUIRES_REVIEW", "UNDER_REVIEW"],  # Legacy compatibility
}


def validate_status_transition(
    current_status: str,
    target_status: str,
    reopen_reason: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Validate whether a candidate state transition is legally permitted.

    Rules:
        - REQUIRES_REVIEW -> UNDER_REVIEW (Valid: review started)
        - UNDER_REVIEW -> REVIEWED (Valid: review completed with notes)
        - UNDER_REVIEW -> DISMISSED (Valid: dismissed with rationale)
        - UNDER_REVIEW -> REQUIRES_REVIEW (Valid: paused/returned to queue)
        - REQUIRES_REVIEW -> REVIEWED (INVALID: cannot skip deliberate review)
        - REQUIRES_REVIEW -> DISMISSED (INVALID: cannot dismiss without review)
        - DISMISSED -> REVIEWED (INVALID: cannot jump between terminal states)
        - REVIEWED -> DISMISSED (INVALID: cannot jump between terminal states)
        - Terminal -> UNDER_REVIEW (Valid ONLY with explicit non-empty reopen_reason)
    """
    curr = current_status.upper()
    target = target_status.upper()

    if curr == target:
        return True, None

    allowed = VALID_TRANSITIONS.get(curr, [])
    if target not in allowed:
        return (
            False,
            f"Invalid transition: Illegal status transition from '{curr}' to '{target}'. "
            f"Permitted next states from '{curr}': {allowed}.",
        )

    # Enforce mandatory rationale when reopening from terminal states
    if curr in ("REVIEWED", "DISMISSED") and target == "UNDER_REVIEW":
        if not reopen_reason or not reopen_reason.strip():
            return (
                False,
                f"Reopening an incident from '{curr}' to 'UNDER_REVIEW' requires an explicit, non-empty reopen_reason.",
            )

    return True, None


# ==============================================================================
# 2. Canonical Identity & Idempotent Deduplication
# ==============================================================================

def compute_canonical_fingerprint(candidate: CandidateDossier) -> str:
    """Compute a deterministic, invariant identity string for a candidate episode.

    Sorts driver pair alphabetically so that (A vs B) == (B vs A).
    Includes session, lap, peak timestamp, and detection method.
    """
    sorted_pair = "_".join(sorted([candidate.driver_a.upper(), candidate.driver_b.upper()]))
    # Clean peak timestamp to second-level resolution to absorb sub-centisecond shifts
    peak_clean = candidate.event_peak.split(".")[0].replace(" ", "T")
    sess_id = candidate.session_id.lower().strip()
    lap = candidate.lap_number_a or 0
    return f"MII::{sess_id}::{sorted_pair}::L{lap}::{peak_clean}::{candidate.detection_method}"


# ==============================================================================
# 3. Candidate Persistence Service
# ==============================================================================

class CandidatePersistenceService:
    """Manages the persistence of algorithmic candidates into the database."""

    @staticmethod
    def ensure_session_prerequisites(db: Session, session_id: str) -> DBSession:
        """Ensure parent Race and Session records exist in DB to satisfy foreign keys."""
        sess = db.get(DBSession, session_id)
        if sess:
            return sess

        # Extract season and grand prix name if parsable, e.g. f1-2024-italian grand prix-race
        race_id = "f1-2024-monza"
        race_name = "Italian Grand Prix"
        season_str = "2024"

        race = db.get(Race, race_id)
        if not race:
            race = Race(
                id=race_id,
                series="Formula 1",
                season=season_str,
                round=16,
                name=race_name,
                circuit="Monza",
                country="Italy",
                city="Monza",
                source="fastf1",
            )
            db.add(race)
            db.flush()

        sess = DBSession(
            id=session_id,
            race_id=race_id,
            session_type="Race",
            name=f"{race_name} 2024 — Race",
            status="ANALYSIS_READY",
            source="fastf1",
        )
        db.add(sess)
        db.flush()
        return sess

    @staticmethod
    def ensure_driver_prerequisites(db: Session, session_id: str, driver_code: str) -> Driver:
        """Ensure driver participation record exists in drivers table."""
        code = driver_code.upper().strip()
        drv_id = f"{session_id}-{code.lower()}"
        driver = db.get(Driver, drv_id)
        if driver:
            return driver

        # Fallback metadata mapping
        driver_defaults = {
            "RIC": ("Daniel Ricciardo", 3, "RB", "#6692FF"),
            "HUL": ("Nico Hulkenberg", 27, "Haas F1 Team", "#B6BABD"),
            "TSU": ("Yuki Tsunoda", 22, "RB", "#6692FF"),
            "MAG": ("Kevin Magnussen", 20, "Haas F1 Team", "#B6BABD"),
            "GAS": ("Pierre Gasly", 10, "Alpine", "#0093CC"),
            "VER": ("Max Verstappen", 1, "Red Bull Racing", "#3671C6"),
            "NOR": ("Lando Norris", 4, "McLaren", "#FF8000"),
            "LEC": ("Charles Leclerc", 16, "Ferrari", "#E80020"),
            "SAI": ("Carlos Sainz", 55, "Ferrari", "#E80020"),
            "HAM": ("Lewis Hamilton", 44, "Mercedes", "#27F4D2"),
            "RUS": ("George Russell", 63, "Mercedes", "#27F4D2"),
            "PIA": ("Oscar Piastri", 81, "McLaren", "#FF8000"),
            "PER": ("Sergio Perez", 11, "Red Bull Racing", "#3671C6"),
            "ALB": ("Alexander Albon", 23, "Williams", "#64C4FF"),
            "COL": ("Franco Colapinto", 43, "Williams", "#64C4FF"),
            "ALO": ("Fernando Alonso", 14, "Aston Martin", "#229971"),
            "STR": ("Lance Stroll", 18, "Aston Martin", "#229971"),
            "BOT": ("Valtteri Bottas", 77, "Kick Sauber", "#52E252"),
            "ZHO": ("Guanyu Zhou", 24, "Kick Sauber", "#52E252"),
            "OCO": ("Esteban Ocon", 31, "Alpine", "#0093CC"),
        }

        full_name, number, team, color = driver_defaults.get(
            code, (f"Driver {code}", 99, "Formula 1 Team", "#FFFFFF")
        )

        driver = Driver(
            id=drv_id,
            session_id=session_id,
            code=code,
            number=number,
            full_name=full_name,
            abbreviation=code,
            team=team,
            team_color=color,
            source="fastf1",
        )
        db.add(driver)
        db.flush()
        return driver

    @classmethod
    def persist_candidate(
        cls,
        db: Session,
        candidate: CandidateDossier,
        session_id: Optional[str] = None,
        reviewer_id: str = "system-ingest",
        initial_notes: Optional[str] = None,
    ) -> Tuple[Incident, bool]:
        """Persist a reconstructed CandidateDossier idempotently into the incidents table.

        Returns:
            Tuple of (Incident, is_created: bool)
            If candidate already exists with same canonical fingerprint, returns (existing, False).
        """
        fingerprint = compute_canonical_fingerprint(candidate)
        target_session = session_id or candidate.session_id

        # 1. Idempotency Check via Canonical Fingerprint
        stmt = select(Incident).where(
            (Incident.canonical_fingerprint == fingerprint)
            | (Incident.candidate_id == candidate.candidate_id)
        )
        existing = db.scalars(stmt).first()
        if existing:
            logger.info(f"Candidate '{candidate.candidate_id}' already persisted as incident '{existing.id}'")
            return existing, False

        # 2. Transactional Persistence
        try:
            # Ensure prerequisites exist
            cls.ensure_session_prerequisites(db, target_session)
            drv_a = cls.ensure_driver_prerequisites(db, target_session, candidate.driver_a)
            drv_b = cls.ensure_driver_prerequisites(db, target_session, candidate.driver_b)

            incident_id = f"INC-{candidate.candidate_id.replace('CAND-', '')}"
            # Check if this primary key is already taken (edge case fallback)
            collision = db.get(Incident, incident_id)
            if collision:
                incident_id = f"{incident_id}-{int(time.time())}"

            # Create Incident Record
            now = datetime.now(timezone.utc)
            incident = Incident(
                id=incident_id,
                session_id=target_session,
                incident_type=candidate.event_type.value,
                status=ReviewStatus.REQUIRES_REVIEW.value,
                severity="HIGH" if candidate.event_type == CandidateEventType.CONTACT_CANDIDATE else "MEDIUM",
                lap=candidate.lap_number_a or 1,
                turn=candidate.turn or "Track Sector",
                timestamp_str=candidate.event_peak,
                summary=candidate.summary,
                detection_method=candidate.detection_method,
                evidence_strength=candidate.evidence_strength,
                analysis_version="reconstruction_v1",
                candidate_id=candidate.candidate_id,
                canonical_fingerprint=fingerprint,
                preprocessing_version=candidate.preprocessing_version,
                data_quality_summary=candidate.data_quality_flags.quality_summary,
                minimum_gap_meters=candidate.minimum_gap_meters,
                peak_closing_speed_ms=candidate.peak_closing_speed_ms,
                dossier_data=json.dumps({
                    "candidate_id": candidate.candidate_id,
                    "event_start": candidate.event_start,
                    "event_peak": candidate.event_peak,
                    "event_end": candidate.event_end,
                    "duration_seconds": candidate.duration_seconds,
                    "minimum_gap_meters": candidate.minimum_gap_meters,
                    "peak_closing_speed_ms": candidate.peak_closing_speed_ms,
                    "evidence_strength": candidate.evidence_strength,
                }),
                video_available=False,
                telemetry_available=True,
                regulations_available=True,
                source="fastf1",
                source_id=candidate.candidate_id,
            )
            db.add(incident)
            db.flush()

            # Associate Participating Drivers with Strictly Neutral Roles
            assoc_a = IncidentDriver(
                incident_id=incident.id,
                driver_id=drv_a.id,
                role="PRIMARY",
            )
            assoc_b = IncidentDriver(
                incident_id=incident.id,
                driver_id=drv_b.id,
                role="SECONDARY",
            )
            db.add(assoc_a)
            db.add(assoc_b)

            # Create Initial Review Record Audit Entry
            rev_id = f"REV-{incident.id}-INIT-{uuid.uuid4().hex[:6]}"
            initial_review = ReviewRecord(
                id=rev_id,
                incident_id=incident.id,
                status=ReviewStatus.REQUIRES_REVIEW.value,
                reviewer_id=reviewer_id,
                review_notes=initial_notes or "Algorithmic candidate reconstructed and queued for steward review.",
                observations=f"Minimum proximity observed: {candidate.minimum_gap_meters}m. Closing speed: {candidate.peak_closing_speed_ms}m/s.",
            )
            db.add(initial_review)

            db.commit()
            db.refresh(incident)
            logger.info(f"Successfully persisted new candidate '{candidate.candidate_id}' as incident '{incident.id}'")
            return incident, True

        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed while persisting candidate '{candidate.candidate_id}': {e}")
            raise

    @classmethod
    def persist_by_candidate_id(
        cls,
        db: Session,
        candidate_id: str,
        session_id: Optional[str] = None,
        reviewer_id: str = "system-ingest",
        notes: Optional[str] = None,
    ) -> CandidatePersistResponse:
        """Resolve a candidate by ID via the reconstruction engine and persist it."""
        engine = get_reconstruction_engine()
        dossier = engine.get_candidate_dossier(candidate_id)
        if not dossier:
            raise ResourceNotFoundException("CandidateDossier", candidate_id)

        inc, is_created = cls.persist_candidate(
            db=db,
            candidate=dossier.candidate,
            session_id=session_id or dossier.session_id,
            reviewer_id=reviewer_id,
            initial_notes=notes,
        )

        return CandidatePersistResponse(
            incident_id=inc.id,
            candidate_id=inc.candidate_id or candidate_id,
            canonical_fingerprint=inc.canonical_fingerprint or "",
            status=ReviewStatus(inc.status),
            is_created=is_created,
            created_at=inc.created_at.isoformat() if inc.created_at else datetime.now(timezone.utc).isoformat(),
            message="New incident created" if is_created else "Candidate already persisted (idempotent match)",
        )

    @classmethod
    def persist_bulk_candidates(
        cls,
        db: Session,
        request: BulkCandidatePersistRequest,
    ) -> BulkCandidatePersistResponse:
        """Execute bounded bulk candidate persistence."""
        t0 = time.time()
        engine = get_reconstruction_engine()
        persisted: List[CandidatePersistResponse] = []
        created_count = 0
        existing_count = 0
        failed_count = 0

        # Case A: Specific candidate IDs provided
        if request.candidate_ids:
            for cid in request.candidate_ids[: request.limit]:
                try:
                    res = cls.persist_by_candidate_id(db, cid, session_id=None)
                    persisted.append(res)
                    if res.is_created:
                        created_count += 1
                    else:
                        existing_count += 1
                except Exception as e:
                    logger.warning(f"Bulk persist failed for candidate {cid}: {e}")
                    failed_count += 1
        else:
            # Case B: Reconstruct driver pairs for session and persist
            pairs = request.driver_pairs or [
                ["RIC", "HUL"],
                ["HUL", "TSU"],
                ["MAG", "GAS"],
            ]
            total_processed = 0
            for drv_a, drv_b in pairs:
                if total_processed >= request.limit:
                    break
                try:
                    cands = engine.reconstruct_pair_candidates(
                        season=request.season,
                        round_or_name=request.round_or_name,
                        session_identifier=request.session,
                        driver_a=drv_a,
                        driver_b=drv_b,
                        lap=request.lap,
                    )
                    for cand in cands:
                        if total_processed >= request.limit:
                            break
                        total_processed += 1
                        inc, is_created = cls.persist_candidate(db, cand)
                        res = CandidatePersistResponse(
                            incident_id=inc.id,
                            candidate_id=inc.candidate_id or cand.candidate_id,
                            canonical_fingerprint=inc.canonical_fingerprint or "",
                            status=ReviewStatus(inc.status),
                            is_created=is_created,
                            created_at=inc.created_at.isoformat() if inc.created_at else datetime.now(timezone.utc).isoformat(),
                            message="New incident created" if is_created else "Candidate already persisted (idempotent match)",
                        )
                        persisted.append(res)
                        if is_created:
                            created_count += 1
                        else:
                            existing_count += 1
                except Exception as e:
                    logger.warning(f"Error evaluating pair {drv_a} vs {drv_b} in bulk persist: {e}")
                    failed_count += 1

        elapsed = round(time.time() - t0, 3)
        return BulkCandidatePersistResponse(
            total_requested=len(persisted) + failed_count,
            created=created_count,
            already_existing=existing_count,
            failed=failed_count,
            persisted_incidents=persisted,
            execution_time_sec=elapsed,
        )

    @classmethod
    def transition_status(
        cls,
        db: Session,
        incident_id: str,
        payload: ReviewCreateRequest,
    ) -> Tuple[Incident, ReviewRecord]:
        """Execute a validated human steward review state transition."""
        inc = db.get(Incident, incident_id)
        if not inc:
            raise ResourceNotFoundException("Incident", incident_id)

        target_status = payload.status.value.upper()
        current_status = inc.status.upper()

        is_valid, error_msg = validate_status_transition(
            current_status=current_status,
            target_status=target_status,
            reopen_reason=payload.reopen_reason,
        )
        if not is_valid:
            raise ValidationException(
                message=error_msg or "Invalid state transition",
                details={
                    "current_status": current_status,
                    "target_status": target_status,
                    "allowed_transitions": VALID_TRANSITIONS.get(current_status, []),
                },
            )

        now = datetime.now(timezone.utc)
        review_id = f"REV-{incident_id}-{int(now.timestamp())}-{uuid.uuid4().hex[:6]}"

        # Timestamps management
        started_at = now if target_status == ReviewStatus.UNDER_REVIEW.value else None
        completed_at = now if target_status in (ReviewStatus.REVIEWED.value, ReviewStatus.DISMISSED.value) else None

        def _fmt(val: Optional[Union[str, List[str]]]) -> Optional[str]:
            if val is None:
                return None
            if isinstance(val, list):
                return ", ".join(str(x) for x in val)
            return str(val)

        reopen_str = payload.reopen_reason.strip() if payload.reopen_reason else None
        obs_val = _fmt(payload.observations)
        if reopen_str and not obs_val:
            obs_val = f"Reopen justification: {reopen_str}"

        notes_val = payload.review_notes
        if reopen_str and not notes_val:
            notes_val = f"Review reopened: {reopen_str}"

        rationale_val = payload.review_rationale or reopen_str

        review = ReviewRecord(
            id=review_id,
            incident_id=incident_id,
            status=target_status,
            reviewer_id=payload.reviewer_id,
            review_started_at=started_at,
            review_completed_at=completed_at,
            evidence_considered=_fmt(payload.evidence_considered),
            evidence_missing=_fmt(payload.evidence_missing),
            observations=obs_val,
            review_notes=notes_val,
            review_rationale=rationale_val,
            regulatory_references="; ".join(payload.regulatory_references) if payload.regulatory_references else None,
        )

        inc.status = target_status
        db.add(review)
        db.commit()
        db.refresh(inc)
        db.refresh(review)

        return inc, review

    @staticmethod
    def get_incident_reviews(db: Session, incident_id: str) -> List[ReviewRecord]:
        """Retrieve complete chronological review record audit trail for an incident."""
        stmt = (
            select(ReviewRecord)
            .where(ReviewRecord.incident_id == incident_id)
            .order_by(ReviewRecord.created_at.asc())
        )
        return list(db.scalars(stmt).all())
