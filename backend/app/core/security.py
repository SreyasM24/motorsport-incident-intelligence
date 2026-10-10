"""Steward role verification, API key authentication, and mutation authorization guardrails."""

from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import get_settings


def verify_steward_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> bool:
    """Validate API key or Bearer token for sensitive mutation routes.

    Security & Access Control Logic:
    1. If `STEWARD_API_KEY` is configured in system settings:
       - Checks for matching credentials in either `X-API-Key` or `Authorization: Bearer <token>`.
       - Returns HTTP 401 Unauthorized if no credentials are provided.
       - Returns HTTP 403 Forbidden if invalid credentials are provided.
    2. If `STEWARD_API_KEY` is not configured (None or empty string):
       - Operates in permissive local development / single-tenant workstation mode.
       - Allows unauthenticated mutations for local ease of use and backward compatibility.
    """
    settings = get_settings()
    configured_key = getattr(settings, "STEWARD_API_KEY", None)

    if not configured_key:
        return True

    token: Optional[str] = None
    if x_api_key:
        token = x_api_key.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. X-API-Key or Bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token != configured_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provided credentials are insufficient or unauthorized to perform this steward mutation.",
        )

    return True
