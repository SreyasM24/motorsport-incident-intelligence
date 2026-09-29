"""Structured logging configuration for Motorsport Incident Intelligence."""

import logging
import sys
from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure structured logging across standard library loggers."""
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Quiet external third-party chatty loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    return logger


logger = logging.getLogger("app")
