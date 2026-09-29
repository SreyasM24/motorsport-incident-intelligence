"""Production-quality OpenF1 HTTP client with bounded queries, retry logic, and logging."""

import time
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import get_settings
from app.core.logging import logger
from app.data.openf1.exceptions import (
    OpenF1Error,
    OpenF1RateLimitError,
    OpenF1ResourceNotFoundError,
    OpenF1TimeoutError,
)


class OpenF1Client:
    """HTTP client for querying the official OpenF1 REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 15.0,
        max_retries: int = 3,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.OPENF1_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._sync_client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Lazy-initialize reusable sync client."""
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"User-Agent": "Motorsport-Incident-Intelligence/1.0"},
            )
        return self._sync_client

    def close(self):
        """Close open HTTP connections."""
        if self._sync_client and not self._sync_client.is_closed:
            self._sync_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform bounded GET request with exponential retry on rate limits and 5xx."""
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        client = self._get_client()

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"OpenF1: GET {endpoint} with {clean_params} (attempt {attempt})")
                response = client.get(endpoint, params=clean_params)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2))
                    logger.warning(f"OpenF1 429 rate limit hit. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    last_error = OpenF1RateLimitError(retry_after=retry_after)
                    continue

                if response.status_code == 404:
                    return []

                response.raise_for_status()
                data = response.json()
                if not isinstance(data, list):
                    return [data] if data else []
                return data

            except httpx.TimeoutException as e:
                logger.warning(f"OpenF1: Timeout on attempt {attempt}: {e}")
                last_error = OpenF1TimeoutError(url=f"{self.base_url}/{endpoint}", timeout_seconds=self.timeout)
                time.sleep(1.0 * attempt)
            except httpx.HTTPStatusError as e:
                logger.warning(f"OpenF1 HTTP status error {e.response.status_code}: {e}")
                if e.response.status_code >= 500:
                    time.sleep(1.0 * attempt)
                    last_error = OpenF1Error(
                        message=f"OpenF1 server error {e.response.status_code}",
                        status_code=e.response.status_code,
                    )
                    continue
                raise OpenF1Error(
                    message=f"OpenF1 request error: {e}",
                    status_code=e.response.status_code,
                ) from e
            except Exception as e:
                logger.error(f"OpenF1 unexpected error: {e}")
                raise OpenF1Error(message=f"Unexpected OpenF1 error: {e}") from e

        if last_error:
            raise last_error
        return []

    # -------------------------------------------------------------------------
    # Reusable Resource Queries
    # -------------------------------------------------------------------------

    def get_sessions(
        self,
        year: Optional[int] = None,
        country_name: Optional[str] = None,
        circuit_short_name: Optional[str] = None,
        session_type: Optional[str] = None,
        session_name: Optional[str] = None,
        session_key: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve sessions matching specified filter criteria."""
        params = {
            "year": year,
            "country_name": country_name,
            "circuit_short_name": circuit_short_name,
            "session_type": session_type,
            "session_name": session_name,
            "session_key": session_key,
        }
        return self._request("sessions", params=params)

    def get_drivers(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve drivers for a specific session."""
        params = {"session_key": session_key, "driver_number": driver_number}
        return self._request("drivers", params=params)

    def get_car_data(
        self,
        session_key: int,
        driver_number: int,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        limit: Optional[int] = 500,
    ) -> List[Dict[str, Any]]:
        """Retrieve bounded high-frequency car telemetry (speed, rpm, throttle, brake)."""
        params = {
            "session_key": session_key,
            "driver_number": driver_number,
        }
        if date_start:
            params["date>="] = date_start
        if date_end:
            params["date<="] = date_end
        # OpenF1 returns all records matching query; slice locally if limit specified
        results = self._request("car_data", params=params)
        return results[:limit] if limit and len(results) > limit else results

    def get_location(
        self,
        session_key: int,
        driver_number: int,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        limit: Optional[int] = 500,
    ) -> List[Dict[str, Any]]:
        """Retrieve bounded 3D spatial coordinate data (x, y, z)."""
        params = {
            "session_key": session_key,
            "driver_number": driver_number,
        }
        if date_start:
            params["date>="] = date_start
        if date_end:
            params["date<="] = date_end
        results = self._request("location", params=params)
        return results[:limit] if limit and len(results) > limit else results

    def get_laps(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve lap timing and sector duration records."""
        params = {
            "session_key": session_key,
            "driver_number": driver_number,
            "lap_number": lap_number,
        }
        return self._request("laps", params=params)

    def get_race_control_messages(
        self,
        session_key: int,
        flag: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve FIA race control messages, flags, safety car deployments."""
        params = {
            "session_key": session_key,
            "flag": flag,
            "category": category,
        }
        return self._request("race_control", params=params)
