"""Health diagnostics, liveness, and readiness endpoints."""

import os
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from app.core.config import get_settings
from app.database.connection import check_db_connection
from app.schemas.common import HealthResponse, LivenessResponse, ReadinessResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="System Health & Integration Diagnostics")
async def get_health() -> HealthResponse:
    """Return health status of the application, database, and local caching services."""
    settings = get_settings()

    # FastF1 cache directory check
    cache_path = os.path.abspath(settings.FASTF1_CACHE_DIR)
    cache_ready = os.path.exists(cache_path) and os.access(cache_path, os.W_OK)
    if not os.path.exists(cache_path):
        try:
            os.makedirs(cache_path, exist_ok=True)
            cache_ready = True
        except Exception:
            cache_ready = False

    # Database connectivity check
    db_connected, _ = check_db_connection()

    overall_status = "healthy" if db_connected and cache_ready else "degraded"

    return HealthResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        api_prefix=settings.API_V1_PREFIX,
        database_connected=db_connected,
        fastf1_cache_ready=cache_ready,
        fastf1_cache_dir=cache_path,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/health/live", response_model=LivenessResponse, summary="Liveness Probe")
async def get_liveness() -> LivenessResponse:
    """Non-blocking liveness probe to verify the application process is running."""
    settings = get_settings()
    return LivenessResponse(
        status="alive",
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/health/ready", response_model=ReadinessResponse, summary="Readiness Probe")
async def get_readiness(response: Response) -> ReadinessResponse:
    """Readiness probe verifying database connectivity and critical dependency availability."""
    settings = get_settings()

    # Check database
    db_connected, db_msg = check_db_connection()

    # Check cache directory
    cache_path = os.path.abspath(settings.FASTF1_CACHE_DIR)
    cache_ready = os.path.exists(cache_path) and os.access(cache_path, os.W_OK)
    if not os.path.exists(cache_path):
        try:
            os.makedirs(cache_path, exist_ok=True)
            cache_ready = True
        except Exception:
            cache_ready = False

    is_ready = db_connected and cache_ready
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        database_ready=db_connected,
        cache_ready=cache_ready,
        details={
            "database_message": db_msg,
            "cache_dir": cache_path,
        },
        timestamp=datetime.now(timezone.utc),
    )
