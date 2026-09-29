"""OpenF1 client and ingestion exceptions."""

from app.core.exceptions import AppException


class OpenF1Error(AppException):
    """Base exception for all OpenF1 API communications."""
    def __init__(self, message: str, status_code: int = 502, details: dict = None):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="OPENF1_ERROR",
            details=details,
        )


class OpenF1RateLimitError(OpenF1Error):
    """Raised when OpenF1 returns HTTP 429 Too Many Requests."""
    def __init__(self, retry_after: int = 5):
        super().__init__(
            message=f"OpenF1 rate limit exceeded. Retry after {retry_after} seconds.",
            status_code=429,
            details={"retry_after_seconds": retry_after},
        )
        self.error_code = "OPENF1_RATE_LIMIT"


class OpenF1ResourceNotFoundError(OpenF1Error):
    """Raised when an OpenF1 endpoint returns no data for a bounded query."""
    def __init__(self, resource: str, params: dict):
        super().__init__(
            message=f"No OpenF1 data found for resource '{resource}' with params {params}",
            status_code=404,
            details={"resource": resource, "params": params},
        )
        self.error_code = "OPENF1_NOT_FOUND"


class OpenF1TimeoutError(OpenF1Error):
    """Raised when an OpenF1 network request times out."""
    def __init__(self, url: str, timeout_seconds: float):
        super().__init__(
            message=f"OpenF1 request timed out after {timeout_seconds}s: {url}",
            status_code=504,
            details={"url": url, "timeout_seconds": timeout_seconds},
        )
        self.error_code = "OPENF1_TIMEOUT"
