"""API router for sporting regulations and judicial precedents."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.connection import get_db
from app.models.regulation import Regulation
from app.schemas.regulation import RegulationSchema, RegulationListResponse
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/regulations", tags=["Regulations"])


@router.get("", response_model=List[RegulationSchema], summary="Search and list regulations")
def get_regulations(
    q: Optional[str] = Query(default=None, description="Search keyword, article number, or topic"),
    series: Optional[str] = Query(default=None, description="Filter by racing series"),
    season: Optional[str] = Query(default=None, description="Filter by championship season"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results returned"),
    db: Session = Depends(get_db),
) -> List[RegulationSchema]:
    """Retrieve normalized FIA Sporting Regulations matching query filters."""
    stmt = select(Regulation)

    if series:
        stmt = stmt.where(Regulation.series == series)
    if season:
        stmt = stmt.where(Regulation.season == season)
    if q:
        q_fmt = f"%{q.lower()}%"
        stmt = stmt.where(
            Regulation.article.ilike(q_fmt)
            | Regulation.title.ilike(q_fmt)
            | Regulation.text.ilike(q_fmt)
            | Regulation.document.ilike(q_fmt)
        )

    stmt = stmt.limit(limit)
    regulations = db.scalars(stmt).all()

    return [
        RegulationSchema(
            id=r.id,
            series=r.series,
            season=r.season,
            document=r.document,
            document_version=r.document_version,
            article=r.article,
            title=r.title,
            text=r.text,
            source_url=r.source_url,
            source=r.source,
        )
        for r in regulations
    ]


@router.get("/{regulation_id}", response_model=RegulationSchema, summary="Get regulation details")
def get_regulation(
    regulation_id: str,
    db: Session = Depends(get_db),
) -> RegulationSchema:
    """Retrieve statutory text and metadata for a specific article ID."""
    reg = db.get(Regulation, regulation_id)
    if not reg:
        raise ResourceNotFoundException("Regulation", regulation_id)

    return RegulationSchema(
        id=reg.id,
        series=reg.series,
        season=reg.season,
        document=reg.document,
        document_version=reg.document_version,
        article=reg.article,
        title=reg.title,
        text=reg.text,
        source_url=reg.source_url,
        source=reg.source,
    )
