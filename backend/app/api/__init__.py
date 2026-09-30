"""API routers package aggregation."""

from fastapi import APIRouter
from app.api import health, races, sessions, drivers, incidents, telemetry, regulations, assistant, analysis, evidence

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(races.router)
api_router.include_router(sessions.router)
api_router.include_router(drivers.router)
api_router.include_router(incidents.router)
api_router.include_router(telemetry.router)
api_router.include_router(regulations.router)
api_router.include_router(assistant.router)
api_router.include_router(analysis.router)
api_router.include_router(evidence.router)

__all__ = ["api_router"]
