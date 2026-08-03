"""Extracts raw student profile data from the WordPress MySQL/MariaDB source.

Usage:
    from src.extractors.wordpress_extractor import WordPressExtractor

    extractor = WordPressExtractor()
    if extractor.test_connection():
        df = extractor.fetch_raw_users()
"""
from __future__ import annotations

import logging
import time

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from config.settings import configure_logging, get_settings

logger = logging.getLogger(__name__)


class WordPressExtractor:
    """Reads student profile rows out of `wp_users` / `wp_usermeta`."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.engine = create_engine(self.settings.wordpress_uri)

    def test_connection(self) -> bool:
        """Ping the WordPress database and log latency, server version, and read access."""
        start = time.perf_counter()
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                version = conn.execute(text("SELECT VERSION()")).scalar_one()
                user_count = conn.execute(text("SELECT COUNT(*) FROM wp_users")).scalar_one()
        except SQLAlchemyError:
            logger.exception("WordPress connection test failed")
            return False

        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "WordPress connection OK | host=%s:%s db=%s | server_version=%s | "
            "wp_users readable (%s rows) | latency=%.1fms",
            self.settings.WP_DB_HOST,
            self.settings.WP_DB_PORT,
            self.settings.WP_DB_NAME,
            version,
            user_count,
            latency_ms,
        )
        return True

    def fetch_raw_users(self) -> pd.DataFrame:
        """Pull `wp_users` joined with `wp_usermeta` as a raw, un-pivoted DataFrame.

        Each row is one (user, meta_key, meta_value) combination — pivoting
        into flat columns happens later in `metadata_pivoter.py`.
        """
        query = text(
            """
            SELECT
                u.ID AS user_id,
                u.user_login,
                u.user_email,
                u.user_registered,
                um.meta_key,
                um.meta_value
            FROM wp_users AS u
            LEFT JOIN wp_usermeta AS um ON um.user_id = u.ID
            """
        )
        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn)

        logger.info("Fetched %d raw wp_users/wp_usermeta rows", len(df))
        return df


if __name__ == "__main__":
    configure_logging()
    extractor = WordPressExtractor()

    print("Testing WordPress connection...")
    ok = extractor.test_connection()
    print(f"Connection status: {'OK' if ok else 'FAILED'}")
