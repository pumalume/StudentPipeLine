"""Inspects the latest raw `ehStudents` snapshot stored in the local data lake.

Usage:
    python -m tests.test_lake_inspection
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

LAKE_WORDPRESS_DIR = Path("data/raw/wordpress")


def _latest_snapshot_dir() -> Path:
    snapshots = sorted(p for p in LAKE_WORDPRESS_DIR.iterdir() if p.is_dir())
    if not snapshots:
        raise FileNotFoundError(
            f"No WordPress snapshots found under {LAKE_WORDPRESS_DIR}. "
            "Run `python -m src.extractors.wordpress_extractor` first."
        )
    return snapshots[-1]


def inspect_latest_snapshot() -> None:
    snapshot_dir = _latest_snapshot_dir()
    print(f"Inspecting snapshot: {snapshot_dir}\n")

    students_file = snapshot_dir / "eh_students.parquet"
    if not students_file.exists():
        raise FileNotFoundError(
            f"Expected {students_file} not found. "
            "Make sure `extract_to_lake()` ran successfully."
        )

    students_df = pd.read_parquet(students_file)

    print(f"Total students in lake: {len(students_df)}")

    print("\nColumns available in eh_students.parquet:")
    for col in students_df.columns:
        print(f" - {col} ({students_df[col].dtype})")

    print("\n" + "=" * 60)
    print("Sample preview: Top 10 student records")
    print("-" * 60)
    print(students_df.head(10).to_string(index=False))


if __name__ == "__main__":
    inspect_latest_snapshot()