"""SQLAlchemy model for motorsport race sessions."""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Session(Base, TimestampMixin):
    """Represents a specific session within an event (e.g., FP1, Quali, Sprint, Race)."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    race_id: Mapped[str] = mapped_column(String(64), ForeignKey("races.id", ondelete="CASCADE"), index=True)
    session_type: Mapped[str] = mapped_column(String(32), index=True, doc="Practice, Qualifying, Sprint, Race")
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_laps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ANALYSIS_READY", index=True)
    source: Mapped[str] = mapped_column(String(32), default="fastf1")
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    race: Mapped["Race"] = relationship("Race", back_populates="sessions")
    drivers: Mapped[List["Driver"]] = relationship("Driver", back_populates="session", cascade="all, delete-orphan")
    incidents: Mapped[List["Incident"]] = relationship("Incident", back_populates="session", cascade="all, delete-orphan")
    telemetry_records: Mapped[List["Telemetry"]] = relationship("Telemetry", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Session id='{self.id}' type='{self.session_type}' name='{self.name}'>"
