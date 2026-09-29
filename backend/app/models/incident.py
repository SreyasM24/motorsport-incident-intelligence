"""SQLAlchemy model for incident candidates and evidence dossiers."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Incident(Base, TimestampMixin):
    """Represents an objective algorithmic incident candidate detected for human steward review.

    CRITICAL DOCTRINE:
        This model represents an evidence candidate. It stores empirical metrics,
        relative motion anomalies, and sensor correlation. It does NOT store guilt,
        fault, penalty, or infringement determinations.
    """

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    incident_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="REQUIRES_REVIEW",
        index=True,
        doc="DETECTED, ANALYZING, REQUIRES_REVIEW, UNDER_REVIEW, REVIEWED",
    )
    severity: Mapped[str] = mapped_column(
        String(16),
        default="MEDIUM",
        index=True,
        doc="LOW, MEDIUM, HIGH, CRITICAL",
    )
    lap: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    turn: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp_str: Mapped[str] = mapped_column(String(32), nullable=False, doc="Formatted time string, e.g. 13:42:18.4")
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Track coordinates
    track_position: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    z: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detection_method: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # Evidence Strength (0 - 100). NOT probability of guilt/infringement!
    evidence_strength: Mapped[int] = mapped_column(
        Integer,
        default=50,
        doc="Algorithmic correlation confidence score 0-100; strictly denotes sensor alignment strength.",
    )
    analysis_version: Mapped[Optional[str]] = mapped_column(String(32), default="v1.0")

    # Media and evidence availability indicators
    video_available: Mapped[bool] = mapped_column(Boolean, default=False)
    video_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    telemetry_available: Mapped[bool] = mapped_column(Boolean, default=True)
    regulations_available: Mapped[bool] = mapped_column(Boolean, default=True)

    source: Mapped[str] = mapped_column(String(32), default="fastf1")
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Candidate provenance and idempotent deduplication
    candidate_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    canonical_fingerprint: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    preprocessing_version: Mapped[Optional[str]] = mapped_column(String(32), default="telemetry_preprocessing_v1")
    data_quality_summary: Mapped[Optional[str]] = mapped_column(String(64), default="FULL_FIDELITY")
    minimum_gap_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    peak_closing_speed_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dossier_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="JSON serialized reproducible dossier summary")

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="incidents")
    drivers_involved: Mapped[List["IncidentDriver"]] = relationship(
        "IncidentDriver", back_populates="incident", cascade="all, delete-orphan"
    )
    reviews: Mapped[List["ReviewRecord"]] = relationship(
        "ReviewRecord", back_populates="incident", cascade="all, delete-orphan", order_by="ReviewRecord.created_at.desc()"
    )

    def __repr__(self) -> str:
        return f"<Incident id='{self.id}' type='{self.incident_type}' lap={self.lap} status='{self.status}'>"
