"""Verifies the PostgreSQL connection settings work.

Usage:
    python -m tests.test_postgres_connection
"""
from __future__ import annotations

from config.settings import configure_logging
from src.database.connection import test_postgres_connection


def main() -> None:
    configure_logging()

    print("Testing PostgreSQL connection...")
    ok = test_postgres_connection()

    if ok:
        print("PostgreSQL connection: SUCCESS")
    else:
        print("PostgreSQL connection: FAILED (see logs above for details)")


if __name__ == "__main__":
    main()
