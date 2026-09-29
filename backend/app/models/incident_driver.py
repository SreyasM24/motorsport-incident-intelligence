"""SQLAlchemy association model linking Incidents to involved Drivers."""

from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class IncidentDriver(Base, TimestampMixin):
    """Associates an Incident with participating drivers using strictly neutral roles.

    Note:
        Roles must NEVER designate guilt or fault. Valid neutral values:
        - 'INVOLVED': Standard participant in the interaction window
        - 'PRIMARY': Focal driver designated for telemetry comparison reference
        - 'SECONDARY': Adjacent driver designated for relative motion baseline
    """

    __tablename__ = "incident_drivers"
    __table_args__ = (
        UniqueConstraint("incident_id", "driver_id", name="uq_incident_driver"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    driver_id: Mapped[str] = mapped_column(String(64), ForeignKey("drivers.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(
        String(32),
        default="INVOLVED",
        doc="Neutral interaction role: INVOLVED, PRIMARY, or SECONDARY",
    )

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="drivers_involved")
    driver: Mapped["Driver"] = relationship("Driver", back_populates="incident_participations")

    def __repr__(self) -> str:
        return f"<IncidentDriver incident='{self.incident_id}' driver='{self.driver_id}' role='{self.role}'>"
