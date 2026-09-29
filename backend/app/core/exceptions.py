"""API error models and custom exception definitions."""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging import logger


class AppException(Exception):
    """Base application exception for managed API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ResourceNotFoundException(AppException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ValidationException(AppException):
    """Exception raised when domain validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            error_code="VALIDATION_ERROR",
            details=details,
        )


class DatabaseConnectionException(AppException):
    """Exception raised when database connection fails or is unavailable."""

    def __init__(self, message: str = "Database connection failed or database is unavailable."):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_UNAVAILABLE",
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform JSON error handlers with the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            f"API error [{exc.error_code}] on {request.method} {request.url.path}: {exc.message}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "status_code": exc.status_code,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(f"Request validation failed on {request.method} {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "REQUEST_VALIDATION_ERROR",
                    "message": "The request body or parameters failed schema validation.",
                    "status_code": 422,
                    "details": {"validation_errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled internal server error on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please consult system logs.",
                    "status_code": 500,
                    "details": {},
                }
            },
        )
