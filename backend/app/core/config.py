"""Application configuration module using pydantic-settings."""

import os
from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    APP_NAME: str = Field(default="Motorsport Incident Intelligence API", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="SemVer version")
    ENVIRONMENT: str = Field(default="development", description="Runtime environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    API_V1_PREFIX: str = Field(default="/api/v1", description="URL prefix for v1 API routes")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/motorsport_intelligence",
        description="SQLAlchemy database connection string",
    )

    # Ingestion & external services
    FASTF1_CACHE_DIR: str = Field(
        default="data/cache/fastf1",
        description="Local directory for FastF1 cache",
    )
    OPENF1_BASE_URL: str = Field(
        default="https://api.openf1.org/v1",
        description="Base URL for OpenF1 API",
    )

    # Telemetry preprocessing analysis grid
    TELEMETRY_ANALYSIS_HZ: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Default uniform analysis grid frequency in Hz",
    )
    TELEMETRY_MAX_INTERPOLATION_GAP_MS: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Maximum source gap in ms across which interpolation is permitted",
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
