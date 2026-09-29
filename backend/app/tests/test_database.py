"""Unit tests for database connection mechanics and diagnostic checks."""

from app.database.connection import check_db_connection


def test_check_db_connection_signature():
    """Verify check_db_connection returns a boolean and status string without raising unhandled exceptions."""
    is_connected, msg = check_db_connection()
    assert isinstance(is_connected, bool)
    assert isinstance(msg, str)
    assert len(msg) > 0
