"""SQLAlchemy models for Steward Case Workspace review metadata.

CRITICAL JURISPRUDENTIAL & COMPLIANCE GUARDRAILS:
    1. Human Review Metadata Only: These models persist human steward acknowledgements,
       unresolved questions, and discrepancy annotations.
    2. Non-Mutating of Underlying Evidence: Source telemetry, video calibration, and
       algorithmic candidate records are strictly immutable.
    3. Zero Automated Adjudication: Never stores guilt, fault, or penalty predictions.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class EvidenceAcknowledgement(Base, TimestampMixin):
    """Represents a human steward's explicit evidentiary triage acknowledgement."""

    __tablename__ = "evidence_acknowledgements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(64), index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    evidence_id: Mapped[str] = mapped_column(String(64), index=True)
    reviewer_id: Mapped[str] = mapped_column(String(64), default="steward-panel")
    
    # Allowed actions: CONSIDERED, NOT_RELEVANT, INSUFFICIENT, CONTRADICTORY, REQUIRES_FOLLOW_UP
    action: Mapped[str] = mapped_column(String(32), default="CONSIDERED", index=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    incident: Mapped[Optional["Incident"]] = relationship("Incident")

    def __repr__(self) -> str:
        return f"<EvidenceAcknowledgement id='{self.id}' candidate='{self.candidate_id}' evidence='{self.evidence_id}' action='{self.action}'>"


class UnresolvedQuestion(Base, TimestampMixin):
    """Represents a structured investigation question logged by a human steward."""

    __tablename__ = "unresolved_questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(64), index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="JSON array of related evidence IDs"
    )
    
    # Statuses: OPEN, RESOLVED, DEFERRED
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    reviewer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    incident: Mapped[Optional["Incident"]] = relationship("Incident")

    def __repr__(self) -> str:
        return f"<UnresolvedQuestion id='{self.id}' candidate='{self.candidate_id}' status='{self.status}'>"


class DiscrepancyAnnotation(Base, TimestampMixin):
    """Tracks human steward inspection and resolution status of a cross-modal discrepancy."""

    __tablename__ = "discrepancy_annotations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(64), index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    discrepancy_id: Mapped[str] = mapped_column(String(64), index=True)
    
    # Statuses: OPEN, ACKNOWLEDGED, RESOLVED, UNRESOLVED
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    reviewer_id: Mapped[str] = mapped_column(String(64), default="steward-panel")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    incident: Mapped[Optional["Incident"]] = relationship("Incident")

    def __repr__(self) -> str:
        return f"<DiscrepancyAnnotation id='{self.id}' discrepancy='{self.discrepancy_id}' status='{self.status}'>"
