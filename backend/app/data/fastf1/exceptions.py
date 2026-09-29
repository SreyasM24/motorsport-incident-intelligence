"""FastF1-specific exceptions."""

from app.core.exceptions import AppException


class FastF1Error(AppException):
    """Base exception for all FastF1 data ingestion failures."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, status_code=500, error_code="FASTF1_ERROR", details=details)


class FastF1SessionNotFoundError(FastF1Error):
    """Raised when a requested session is not found in the FastF1 schedule."""
    def __init__(self, season: int, event: str, session: str):
        super().__init__(
            message=f"FastF1 session not found: Season {season}, Event '{event}', Session '{session}'",
            details={"season": season, "event": event, "session": session},
        )
        self.status_code = 404
        self.error_code = "FASTF1_SESSION_NOT_FOUND"


class FastF1DataUnavailableError(FastF1Error):
    """Raised when FastF1 telemetry or timing data is not available for a session."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 404
        self.error_code = "FASTF1_DATA_UNAVAILABLE"


class FastF1CacheError(FastF1Error):
    """Raised when FastF1 cache initialization or access fails."""
    def __init__(self, message: str, cache_dir: str):
        super().__init__(message=message, details={"cache_dir": cache_dir})
        self.error_code = "FASTF1_CACHE_ERROR"
