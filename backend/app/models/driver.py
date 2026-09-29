"""SQLAlchemy model for motorsport drivers in a session."""

from typing import List, Optional
from sqlalchemy import String, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Driver(Base, TimestampMixin):
    """Represents a driver participating in a motorsport session."""

    __tablename__ = "drivers"
    __table_args__ = (
        UniqueConstraint("session_id", "code", name="uq_session_driver_code"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(8), index=True, nullable=False, doc="3-letter code, e.g. VER, HAM")
    number: Mapped[int] = mapped_column(Integer, nullable=False, doc="Driver race car number, e.g. 1, 44")
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    abbreviation: Mapped[str] = mapped_column(String(8), nullable=False)
    nationality: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    team: Mapped[str] = mapped_column(String(128), nullable=False)
    team_color: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, doc="Livery primary hex color code")
    secondary_color: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, doc="Livery secondary hex color code")
    
    # Session aggregate performance statistics
    laps_completed: Mapped[int] = mapped_column(Integer, default=0)
    avg_speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    source: Mapped[str] = mapped_column(String(32), default="fastf1")
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="drivers")
    incident_participations: Mapped[List["IncidentDriver"]] = relationship(
        "IncidentDriver", back_populates="driver", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Driver id='{self.id}' code='{self.code}' #{self.number} team='{self.team}'>"
