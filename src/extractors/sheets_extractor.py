"""Extracts raw student data from the branch Google Sheets into the local data lake.

Each branch (Golcuk, Izmit) has two spreadsheets: a master list and an enrollment
list. Every branch/dataset pair is pulled untouched into its own Parquet snapshot.

Usage:
    from src.extractors.sheets_extractor import GoogleSheetsExtractor

    extractor = GoogleSheetsExtractor()
    if extractor.test_connection():
        paths = extractor.extract_to_lake()
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import SheetSource, configure_logging, get_settings

logger = logging.getLogger(__name__)

LAKE_RAW_DIR = Path("data/raw")

# Read-only is all this extractor ever needs.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _quote_tab(tab: str) -> str:
    """Quote a tab title for use as an A1 range (single quotes are doubled)."""
    escaped = tab.replace("'", "''")
    return f"'{escaped}'"


class GoogleSheetsExtractor:
    """Reads the raw master list and enrollment sheets for every configured branch."""

    def __init__(self, sources: list[SheetSource] | None = None) -> None:
        self.settings = get_settings()
        self.sources = sources if sources is not None else self.settings.sheet_sources

        if not self.sources:
            raise ValueError(
                "No Google Sheets sources configured. Set the GSHEET_<BRANCH>_<DATASET>_ID "
                "variables in your .env (see .env.example) before using GoogleSheetsExtractor."
            )

        missing = self.settings.missing_sheet_sources
        if missing:
            logger.warning(
                "Some branch/dataset pairs have no spreadsheet ID and will be skipped: %s",
                ", ".join(missing),
            )

        credentials = Credentials.from_service_account_file(
            str(self.settings.GOOGLE_CREDENTIALS_FILE), scopes=SCOPES
        )
        self.service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        self._metadata_cache: dict[str, dict] = {}

    # --- Google API plumbing -------------------------------------------------

    def _metadata(self, spreadsheet_id: str) -> dict:
        """Fetch (and cache) spreadsheet metadata: title plus every tab's properties."""
        if spreadsheet_id not in self._metadata_cache:
            self._metadata_cache[spreadsheet_id] = (
                self.service.spreadsheets()
                .get(
                    spreadsheetId=spreadsheet_id,
                    fields="properties.title,sheets.properties(title,gridProperties)",
                )
                .execute()
            )
        return self._metadata_cache[spreadsheet_id]

    def _tab_titles(self, spreadsheet_id: str) -> list[str]:
        return [s["properties"]["title"] for s in self._metadata(spreadsheet_id)["sheets"]]

    def _resolve_tab(self, source: SheetSource) -> str:
        """Return the tab to read for `source`, defaulting to the first tab."""
        titles = self._tab_titles(source.spreadsheet_id)
        if not titles:
            raise ValueError(f"Spreadsheet for {source.key} has no tabs")

        if not source.tab:
            return titles[0]

        if source.tab not in titles:
            raise ValueError(
                f"Tab {source.tab!r} not found for {source.key}. Available tabs: {titles}"
            )
        return source.tab

    # --- Connection check ----------------------------------------------------

    def test_connection(self) -> bool:
        """Verify auth and read access for every configured sheet.

        Logs one line per source and returns True only if all of them succeeded.
        """
        all_ok = True

        for source in self.sources:
            try:
                metadata = self._metadata(source.spreadsheet_id)
                tab = self._resolve_tab(source)
                grid = next(
                    s["properties"].get("gridProperties", {})
                    for s in metadata["sheets"]
                    if s["properties"]["title"] == tab
                )
            except (HttpError, ValueError):
                logger.exception("Google Sheets connection test FAILED for %s", source.key)
                all_ok = False
                continue

            logger.info(
                "Google Sheets OK | %s | spreadsheet=%r | tab=%r | grid=%sx%s",
                source.key,
                metadata.get("properties", {}).get("title", source.spreadsheet_id),
                tab,
                grid.get("rowCount"),
                grid.get("columnCount"),
            )

        return all_ok

    # --- Extraction ----------------------------------------------------------

    def fetch_raw(self, source: SheetSource) -> pd.DataFrame:
        """Pull one sheet's full raw grid into a DataFrame (header row -> columns).

        Zero cleaning or type coercion. Rows shorter than the header row are
        padded with None so every row aligns to the same columns.
        """
        tab = self._resolve_tab(source)
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=source.spreadsheet_id, range=_quote_tab(tab))
            .execute()
        )
        values = result.get("values", [])
        if not values:
            logger.warning("No values returned for %s (tab %r)", source.key, tab)
            return pd.DataFrame()

        headers, *rows = values
        padded_rows = [row + [None] * (len(headers) - len(row)) for row in rows]
        df = pd.DataFrame(padded_rows, columns=headers)

        logger.info("Fetched %d raw rows for %s (tab %r)", len(df), source.key, tab)
        return df

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        """Fetch every configured sheet, keyed by `<branch>/<dataset>`."""
        return {source.key: self.fetch_raw(source) for source in self.sources}

    def extract_to_lake(self) -> dict[str, Path]:
        """Dump every sheet, completely untouched, into the local data lake.

        Writes one Parquet snapshot per source to
        `data/raw/google_sheets/<YYYY-MM-DD>/<branch>/<dataset>.parquet`.
        """
        snapshot_root = LAKE_RAW_DIR / "google_sheets" / date.today().isoformat()
        paths: dict[str, Path] = {}

        for source in self.sources:
            df = self.fetch_raw(source)

            branch_dir = snapshot_root / source.branch
            branch_dir.mkdir(parents=True, exist_ok=True)
            out_path = branch_dir / f"{source.dataset}.parquet"

            df.to_parquet(out_path, index=False)
            logger.info("Saved raw snapshot -> %s (%d rows)", out_path, len(df))
            paths[source.key] = out_path

        return paths


if __name__ == "__main__":
    configure_logging()
    extractor = GoogleSheetsExtractor()

    print(f"Testing Google Sheets connection for {len(extractor.sources)} source(s)...")
    ok = extractor.test_connection()
    print(f"Connection status: {'OK' if ok else 'FAILED'}")

    if ok:
        print("\nExtracting raw snapshots to the data lake...")
        for key, lake_path in extractor.extract_to_lake().items():
            print(f"  {key} -> {lake_path}")
