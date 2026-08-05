"""Verifies the Google Sheets connection and that each branch sheet returns data.

Checks every configured branch/dataset pair: auth + read access first, then an
actual fetch so you can see the shape of what comes back. Nothing is written to
the data lake — this is read-only.

Usage:
    python -m tests.test_sheets_connection
"""
from __future__ import annotations

from config.settings import configure_logging, get_settings
from src.extractors.sheets_extractor import GoogleSheetsExtractor

PREVIEW_ROWS = 5
PREVIEW_COLS = 8


def main() -> None:
    configure_logging()
    settings = get_settings()

    missing = settings.missing_sheet_sources
    if missing:
        print(f"WARNING: no spreadsheet ID configured for: {', '.join(missing)}\n")

    extractor = GoogleSheetsExtractor()
    print(f"Configured sources ({len(extractor.sources)}):")
    for source in extractor.sources:
        tab = source.tab or "<first tab>"
        print(f"  - {source.key:<22} id={source.spreadsheet_id}  tab={tab}")

    print("\nTesting Google Sheets connection...")
    ok = extractor.test_connection()
    print(f"Connection status: {'OK' if ok else 'FAILED (see logs above)'}")

    if not ok:
        return

    print("\nFetching data from each source...")
    failures: list[str] = []

    for source in extractor.sources:
        print("\n" + "=" * 70)
        print(f"{source.key}")
        print("-" * 70)

        try:
            df = extractor.fetch_raw(source)
        except Exception as exc:  # surface the source, keep checking the rest
            print(f"  FETCH FAILED: {type(exc).__name__}: {exc}")
            failures.append(source.key)
            continue

        if df.empty:
            print("  No rows returned (sheet is empty or has only a header row).")
            failures.append(source.key)
            continue

        print(f"  Rows: {len(df)} | Columns: {len(df.columns)}")
        print(f"  Column names: {list(df.columns)}")
        print(f"\n  First {PREVIEW_ROWS} rows (first {PREVIEW_COLS} columns):")
        print(df.iloc[:PREVIEW_ROWS, :PREVIEW_COLS].to_string(index=False))

    print("\n" + "=" * 70)
    if failures:
        print(f"Data fetch: {len(failures)} source(s) returned nothing -> {', '.join(failures)}")
    else:
        print(f"Data fetch: SUCCESS for all {len(extractor.sources)} source(s)")


if __name__ == "__main__":
    main()
