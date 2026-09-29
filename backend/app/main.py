"""FastAPI Application Entry Point for Motorsport Incident Intelligence."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import register_exception_handlers
from app.api import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown lifecycle events."""
    setup_logging()
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]"
    )
    logger.info(f"API Prefix: {settings.API_V1_PREFIX}")
    logger.info(f"CORS Allowed Origins: {settings.CORS_ORIGINS}")
    logger.info(f"FastF1 Cache Directory: {settings.FASTF1_CACHE_DIR}")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")


def create_application() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Decision-support and evidence-intelligence API for Formula 1 & motorsport "
            "incident analysis and human steward review."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Configure custom tracing and request rate protection middleware
    from app.core.middleware import RequestTracingAndLoggingMiddleware, RateLimiterMiddleware
    app.add_middleware(RequestTracingAndLoggingMiddleware)
    app.add_middleware(RateLimiterMiddleware)

    # Register standardized error handlers
    register_exception_handlers(app)


    # Register API v1 routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["Root"])
    async def root():
        """Service discovery entry point."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "operational",
            "docs": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
        }

    return app


app = create_application()
