"""Unit tests for configuration loading and validation."""

from app.core.config import Settings, get_settings


def test_default_settings():
    """Verify default configuration attributes are appropriately set."""
    settings = Settings()
    assert settings.APP_NAME == "Motorsport Incident Intelligence API"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert settings.FASTF1_CACHE_DIR == "data/cache/fastf1"


def test_cors_origins_parsing():
    """Verify comma-separated CORS origins string parses into clean list."""
    settings = Settings(CORS_ORIGINS="http://localhost:3000,http://example.com")
    assert len(settings.CORS_ORIGINS) == 2
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://example.com" in settings.CORS_ORIGINS


def test_get_settings_cached():
    """Verify get_settings returns the singleton cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
