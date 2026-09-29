"""SQLAlchemy model for human steward review records."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class ReviewRecord(Base, TimestampMixin):
    """Represents a human steward review audit entry for an incident candidate.

    CRITICAL DOCTRINE:
        This model records human steward evaluation, notes, and rationale.
        It NEVER records automated AI guilt, fault, or penalty predictions.
    """

    __tablename__ = "review_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default="REQUIRES_REVIEW",
        index=True,
        doc="REQUIRES_REVIEW, UNDER_REVIEW, REVIEWED, DISMISSED",
    )
    reviewer_id: Mapped[str] = mapped_column(
        String(64),
        default="steward-panel",
        doc="Neutral reviewer identifier (e.g. steward-1, FIA-Delegate)",
    )
    review_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Reviewer's structured observations and notes
    evidence_considered: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Summary of evidence channels examined by reviewer"
    )
    evidence_missing: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Summary of missing or inconclusive evidence"
    )
    observations: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Human steward factual observations"
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_rationale: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Explanation for the review determination (REVIEWED or DISMISSED)"
    )
    regulatory_references: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="JSON string or comma-separated list of applicable regulation articles"
    )

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<ReviewRecord id='{self.id}' incident='{self.incident_id}' status='{self.status}' reviewer='{self.reviewer_id}'>"
