"""Inspects the latest raw Google Sheets snapshots stored in the local data lake.

Walks every branch/dataset Parquet file in the most recent snapshot directory.

Usage:
    python -m tests.test_sheets_lake_inspection
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.settings import configure_console_encoding

LAKE_SHEETS_DIR = Path("data/raw/google_sheets")
PREVIEW_ROWS = 10


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

    parquet_files = sorted(snapshot_dir.glob("*/*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(
            f"No Parquet files found under {snapshot_dir}. "
            "Make sure `extract_to_lake()` ran successfully."
        )

    for parquet_file in parquet_files:
        # <snapshot>/<branch>/<dataset>.parquet
        key = f"{parquet_file.parent.name}/{parquet_file.stem}"
        df = pd.read_parquet(parquet_file)

        print("=" * 70)
        print(f"{key}  ({len(df)} rows, {len(df.columns)} columns)")
        print("-" * 70)

        print("Columns:")
        for col in df.columns:
            print(f" - {col} ({df[col].dtype})")

        print(f"\nSample preview: top {PREVIEW_ROWS} records")
        print(df.head(PREVIEW_ROWS).to_string(index=False))
        print()


if __name__ == "__main__":
    configure_console_encoding()
    inspect_latest_snapshot()
