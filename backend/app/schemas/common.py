"""Common, reusable Pydantic v2 schemas."""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    """System and integration health diagnostic payload."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(default="healthy", description="Overall health status: healthy, degraded, or unhealthy")
    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application SemVer version")
    environment: str = Field(..., description="Runtime environment")
    api_prefix: str = Field(..., description="API route prefix")
    database_connected: bool = Field(..., description="True if PostgreSQL database responds to ping")
    fastf1_cache_ready: bool = Field(..., description="True if FastF1 cache directory exists and is writable")
    fastf1_cache_dir: str = Field(..., description="Path to FastF1 cache directory")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Server UTC timestamp")


class LivenessResponse(BaseModel):
    """Application process liveness diagnostic response."""

    status: str = Field(default="alive", description="Liveness status: alive")
    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Server UTC timestamp")


class ReadinessResponse(BaseModel):
    """Application readiness diagnostic response indicating if dependencies are ready."""

    status: str = Field(..., description="Readiness status: ready or not_ready")
    database_ready: bool = Field(..., description="True if database responds")
    cache_ready: bool = Field(..., description="True if cache is writable")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional dependency status details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Server UTC timestamp")



class PaginationParams(BaseModel):
    """Query parameter model for collection pagination."""

    page: int = Field(default=1, ge=1, description="Page number, 1-indexed")
    page_size: int = Field(default=50, ge=1, le=200, description="Items per page, maximum 200")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated list response wrapper."""

    model_config = ConfigDict(from_attributes=True)

    items: List[T] = Field(..., description="List of items for current page")
    total: int = Field(..., ge=0, description="Total count of items matching filter")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Page size limit")
    total_pages: int = Field(..., ge=0, description="Calculated total pages")


class ErrorDetail(BaseModel):
    """Standardized error object structure."""

    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable explanation of error")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional contextual metadata")


class ErrorResponse(BaseModel):
    """Standardized top-level API error envelope."""

    error: ErrorDetail
