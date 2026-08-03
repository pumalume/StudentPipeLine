"""Extracts raw student profile data from the WordPress MySQL/MariaDB source into the Data Lake.

Usage:
    from src.extractors.wordpress_extractor import WordPressExtractor

    extractor = WordPressExtractor()
    if extractor.test_connection():
        paths = extractor.extract_to_lake()
"""
from __future__ import annotations

import logging
import time
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from config.settings import configure_logging, get_settings

logger = logging.getLogger(__name__)

LAKE_RAW_DIR = Path("data/raw")


class WordPressExtractor:
    """Reads student records out of the custom `ehStudents` table."""

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
        """Pull raw student records from the custom `ehStudents` table."""
        query = text(
            """
            SELECT *
            FROM ehStudents
            """
        )
        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn)

        logger.info("Fetched %d raw rows from ehStudents", len(df))
        return df

    def extract_to_lake(self) -> dict[str, Path]:
        """Dump `ehStudents`, completely untouched, into the local data lake.

        Writes Parquet snapshots to `data/raw/wordpress/<YYYY-MM-DD>/eh_students.parquet`.
        """
        snapshot_dir = LAKE_RAW_DIR / "wordpress" / date.today().isoformat()
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        tables = {
            "ehStudents": "eh_students.parquet",
        }

        saved_paths: dict[str, Path] = {}
        with self.engine.connect() as conn:
            for table_name, filename in tables.items():
                df = pd.read_sql(text(f"SELECT * FROM {table_name}"), conn)
                out_path = snapshot_dir / filename
                df.to_parquet(out_path, index=False)
                saved_paths[table_name] = out_path
                logger.info(
                    "Saved raw %s snapshot -> %s (%d rows)", table_name, out_path, len(df)
                )

        return saved_paths


if __name__ == "__main__":
    configure_logging()
    extractor = WordPressExtractor()

    print("Testing WordPress connection...")
    ok = extractor.test_connection()
    print(f"Connection status: {'OK' if ok else 'FAILED'}")

    if ok:
        print("\nExtracting raw snapshots to the data lake...")
        lake_paths = extractor.extract_to_lake()
        for table_name, path in lake_paths.items():
            print(f"  {table_name} -> {path}")