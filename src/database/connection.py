"""Connection helpers for the target PostgreSQL database.

Usage:
    from src.database.connection import test_postgres_connection

    if test_postgres_connection():
        ...
"""
from __future__ import annotations

import logging
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from config.settings import get_settings

logger = logging.getLogger(__name__)


def test_postgres_connection() -> bool:
    """Ping the target PostgreSQL database and log latency, server version, and read access.

    Connects using `Settings.postgres_uri`, executes `SELECT 1` and
    `SELECT VERSION()`, and logs connection status, host, database name,
    server version, and latency.

    Returns True on success, False on any connection/query error.
    """
    settings = get_settings()
    engine = create_engine(settings.postgres_uri)

    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            version = conn.execute(text("SELECT VERSION()")).scalar_one()
    except SQLAlchemyError:
        logger.exception("PostgreSQL connection test failed")
        return False
    finally:
        engine.dispose()

    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "PostgreSQL connection OK | host=%s:%s db=%s | server_version=%s | latency=%.1fms",
        settings.PG_DB_HOST,
        settings.PG_DB_PORT,
        settings.PG_DB_NAME,
        version,
        latency_ms,
    )
    return True
