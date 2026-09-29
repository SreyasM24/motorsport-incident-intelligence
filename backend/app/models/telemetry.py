"""SQLAlchemy model for raw & normalized multi-rate vehicle telemetry."""

from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Telemetry(Base):
    """Stores normalized FastF1/ECU telemetry points for drivers during a session."""

    __tablename__ = "telemetry"
    __table_args__ = (
        Index("ix_telemetry_session_driver_time", "session_id", "driver_id", "timestamp"),
        Index("ix_telemetry_session_lap", "session_id", "lap_number"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    driver_id: Mapped[str] = mapped_column(String(64), ForeignKey("drivers.id", ondelete="CASCADE"), index=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    time_offset: Mapped[float] = mapped_column(Float, doc="Seconds offset relative to lap or session start")
    lap_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    distance: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Lap distance in meters")

    # Spatial coordinates
    x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    z: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Core CAN-bus channels
    speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Speed in km/h")
    throttle: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Throttle percentage 0-100%")
    brake: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Brake pressure/application percentage 0-100%")
    steering: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Steering angle in degrees")
    gear: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    drs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, doc="DRS status indicator")

    # Accelerations / G-forces
    accel_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Lateral acceleration G")
    accel_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, doc="Longitudinal acceleration G")

    source: Mapped[str] = mapped_column(String(32), default="fastf1")

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="telemetry_records")
    driver: Mapped["Driver"] = relationship("Driver")

    def __repr__(self) -> str:
        return f"<Telemetry id={self.id} session='{self.session_id}' driver='{self.driver_id}' speed={self.speed}>"
