"""Production request tracing, structured logging, and endpoint rate limiting middleware."""

import time
import uuid
from typing import Dict, Tuple
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger


class RequestTracingAndLoggingMiddleware(BaseHTTPMiddleware):
    """Assigns unique X-Request-ID, logs structured telemetry, and records latency."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        # Structured diagnostic log
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"REQ [{request_id[:8]}] {request.method} {request.url.path} "
            f"-> {response.status_code} in {duration_ms:.2f}ms (client: {client_ip})"
        )
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """In-memory sliding-window rate limiter protecting expensive analysis and synthesis routes."""

    def __init__(self, app: FastAPI, max_requests_per_window: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests_per_window
        self.window = window_seconds
        # Mapping: ip -> list of timestamps
        self._clients: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exclude static/health routes from rate limiting
        if request.url.path.endswith("/live") or request.url.path.endswith("/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # Clean timestamps older than window
        timestamps = self._clients.get(client_ip, [])
        valid_timestamps = [t for t in timestamps if now - t < self.window]

        # Apply stricter limit on expensive endpoints
        path = request.url.path
        is_expensive = any(sub in path for sub in ("/dossier", "/assistant", "/analysis"))
        limit = 30 if is_expensive else self.max_requests

        if len(valid_timestamps) >= limit:
            retry_after = int(self.window - (now - valid_timestamps[0])) + 1
            logger.warning(
                f"Rate limit exceeded for client {client_ip} on {request.method} {path} "
                f"({len(valid_timestamps)} reqs in window, limit: {limit})"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(max(1, retry_after))},
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many requests. Limit is {limit} requests per minute for this endpoint.",
                        "status_code": 429,
                        "details": {"retry_after_seconds": retry_after, "endpoint": path},
                    }
                },
            )

        valid_timestamps.append(now)
        self._clients[client_ip] = valid_timestamps

        return await call_next(request)
