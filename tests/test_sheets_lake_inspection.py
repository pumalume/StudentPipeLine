"""Inspects the latest raw Google Sheets roster snapshot stored in the local data lake.

Usage:
    python -m tests.test_sheets_lake_inspection
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

LAKE_SHEETS_DIR = Path("data/raw/google_sheets")


def _latest_snapshot_dir() -> Path:
    snapshots = sorted(p for p in LAKE_SHEETS_DIR.iterdir() if p.is_dir())
    if not snapshots:
        raise FileNotFoundError(
            f"No Google Sheets snapshots found under {LAKE_SHEETS_DIR}. "
            "Run `python -m src.extractors.sheets_extractor` first."
        )
    return snapshots[-1]


def inspect_latest_snapshot() -> None:
    snapshot_dir = _latest_snapshot_dir()
    print(f"Inspecting snapshot: {snapshot_dir}\n")

    roster_file = snapshot_dir / "roster.parquet"
    if not roster_file.exists():
        raise FileNotFoundError(
            f"Expected {roster_file} not found. "
            "Make sure `extract_to_lake()` ran successfully."
        )

    roster_df = pd.read_parquet(roster_file)

    print(f"Total roster rows in lake: {len(roster_df)}")

    print("\nColumns available in roster.parquet:")
    for col in roster_df.columns:
        print(f" - {col} ({roster_df[col].dtype})")

    print("\n" + "=" * 60)
    print("Sample preview: Top 10 roster records")
    print("-" * 60)
    print(roster_df.head(10).to_string(index=False))


if __name__ == "__main__":
    inspect_latest_snapshot()
