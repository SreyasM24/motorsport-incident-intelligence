"""FastF1 local filesystem cache configuration and management."""

import os
from pathlib import Path
from typing import Dict, Any
import fastf1
from app.core.config import get_settings
from app.core.logging import logger
from app.data.fastf1.exceptions import FastF1CacheError


def setup_fastf1_cache(custom_dir: str = None) -> str:
    """Initialize and enable the FastF1 persistent cache directory.

    Args:
        custom_dir: Optional custom path overriding settings.FASTF1_CACHE_DIR.

    Returns:
        Absolute path to the enabled cache directory.
    """
    settings = get_settings()
    cache_path_str = custom_dir or settings.FASTF1_CACHE_DIR
    cache_path = Path(cache_path_str).resolve()

    try:
        cache_path.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(cache_path))
        logger.info(f"FastF1 cache enabled at: {cache_path}")
        return str(cache_path)
    except Exception as e:
        logger.error(f"Failed to enable FastF1 cache at {cache_path}: {e}")
        raise FastF1CacheError(
            message=f"Could not initialize FastF1 cache directory: {e}",
            cache_dir=str(cache_path),
        ) from e


def get_cache_status() -> Dict[str, Any]:
    """Inspect the status and disk usage of the FastF1 cache directory."""
    settings = get_settings()
    cache_path = Path(settings.FASTF1_CACHE_DIR).resolve()

    exists = cache_path.exists()
    total_size_bytes = 0
    file_count = 0

    if exists:
        try:
            for item in cache_path.rglob("*"):
                if item.is_file():
                    total_size_bytes += item.stat().st_size
                    file_count += 1
        except Exception as e:
            logger.warning(f"Error calculating FastF1 cache size: {e}")

    return {
        "path": str(cache_path),
        "exists": exists,
        "is_directory": cache_path.is_dir() if exists else False,
        "file_count": file_count,
        "size_bytes": total_size_bytes,
        "size_mb": round(total_size_bytes / (1024 * 1024), 2),
    }
