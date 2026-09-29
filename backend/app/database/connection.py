"""Database connection, session management, and connectivity diagnostics."""

from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.core.config import get_settings
from app.core.logging import logger
from app.core.exceptions import DatabaseConnectionException

settings = get_settings()

# Engine creation with pool pre-ping to detect stale connections
connect_args = {"connect_timeout": 2} if "psycopg" in settings.DATABASE_URL or "postgres" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def check_db_connection() -> Tuple[bool, str]:
    """Check connectivity to PostgreSQL database without raising unhandled errors.

    Returns:
        Tuple of (is_connected: bool, status_message: str)
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connection operational."
    except OperationalError as exc:
        msg = f"PostgreSQL server unreachable or connection refused: {exc.orig if hasattr(exc, 'orig') else exc}"
        logger.warning(f"Database health check failed: {msg}")
        return False, msg
    except Exception as exc:
        msg = f"Unexpected database connection error: {exc}"
        logger.error(f"Database health check error: {msg}")
        return False, msg


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for transactional database sessions.

    Yields:
        Active SQLAlchemy Session.
    Raises:
        DatabaseConnectionException: If PostgreSQL is unreachable.
    """
    db = SessionLocal()
    try:
        yield db
    except OperationalError as exc:
        logger.error(f"Database operational failure during session transaction: {exc}")
        db.rollback()
        raise DatabaseConnectionException(
            f"Database connection error: PostgreSQL is unreachable or timed out."
        ) from exc
    except SQLAlchemyError as exc:
        logger.error(f"Database error during session transaction: {exc}")
        db.rollback()
        raise
    finally:
        db.close()
