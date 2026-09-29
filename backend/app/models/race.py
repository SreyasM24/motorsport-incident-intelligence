"""SQLAlchemy model for motorsport championship races / events."""

from datetime import date
from typing import List, Optional
from sqlalchemy import String, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Race(Base, TimestampMixin):
    """Represents an official championship motorsport event / Grand Prix."""

    __tablename__ = "races"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    series: Mapped[str] = mapped_column(String(64), default="Formula 1", index=True)
    season: Mapped[str] = mapped_column(String(16), index=True)
    round: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    circuit: Mapped[str] = mapped_column(String(128), nullable=False)
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="fastf1")
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="race", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Race id='{self.id}' name='{self.name}' season='{self.season}'>"
