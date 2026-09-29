"""SQLAlchemy model for normalized FIA regulations and sporting code."""

from datetime import date
from typing import Optional
from sqlalchemy import String, Text, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin


class Regulation(Base, TimestampMixin):
    """Represents an official FIA sporting code, technical regulation, or judicial directive."""

    __tablename__ = "regulations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    series: Mapped[str] = mapped_column(String(64), default="Formula 1", index=True)
    season: Mapped[str] = mapped_column(String(16), index=True)
    document: Mapped[str] = mapped_column(String(128), nullable=False, doc="e.g. FIA Sporting Regulations 2024")
    document_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    article: Mapped[str] = mapped_column(String(64), nullable=False, index=True, doc="e.g. Article 33.4")
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, doc="Full statutory text or official regulatory excerpt")
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="FIA World Motor Sport Council")
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<Regulation id='{self.id}' article='{self.article}' title='{self.title[:30]}...'>"
