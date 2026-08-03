"""Extracts raw student roster data from Google Sheets into the local data lake.

Usage:
    from src.extractors.sheets_extractor import GoogleSheetsExtractor

    extractor = GoogleSheetsExtractor()
    if extractor.test_connection():
        path = extractor.extract_to_lake()
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import configure_logging, get_settings

logger = logging.getLogger(__name__)

LAKE_RAW_DIR = Path("data/raw")

# Read-only is all this extractor ever needs.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class GoogleSheetsExtractor:
    """Reads the raw student roster out of a Google Sheet."""

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.GOOGLE_SPREADSHEET_ID:
            raise ValueError(
                "GOOGLE_SPREADSHEET_ID is not set. Add it to your .env before "
                "using GoogleSheetsExtractor."
            )

        credentials = Credentials.from_service_account_file(
            str(self.settings.GOOGLE_CREDENTIALS_FILE), scopes=SCOPES
        )
        self.service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        self.spreadsheet_id = self.settings.GOOGLE_SPREADSHEET_ID

    def _first_sheet_title(self) -> str:
        """Look up the title of the first tab in the spreadsheet."""
        metadata = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        return metadata["sheets"][0]["properties"]["title"]

    def test_connection(self) -> bool:
        """Verify Google API auth and read access to the target spreadsheet."""
        try:
            metadata = (
                self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            )
            sheet_title = metadata["sheets"][0]["properties"]["title"]
            row_count = metadata["sheets"][0]["properties"]["gridProperties"]["rowCount"]
        except HttpError:
            logger.exception("Google Sheets connection test failed")
            return False

        logger.info(
            "Google Sheets connection OK | spreadsheet=%s | first_tab=%r | grid_rows=%s",
            metadata.get("properties", {}).get("title", self.spreadsheet_id),
            sheet_title,
            row_count,
        )
        return True

    def fetch_raw_roster(self) -> pd.DataFrame:
        """Pull the first sheet's full raw grid into a DataFrame (header row -> columns).

        Zero cleaning or type coercion. Rows shorter than the header row are
        padded with None so every row aligns to the same columns.
        """
        sheet_title = self._first_sheet_title()
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_title}'")
            .execute()
        )
        values = result.get("values", [])
        if not values:
            logger.warning("No values returned for sheet %r", sheet_title)
            return pd.DataFrame()

        headers, *rows = values
        padded_rows = [row + [None] * (len(headers) - len(row)) for row in rows]
        df = pd.DataFrame(padded_rows, columns=headers)

        logger.info("Fetched %d raw roster rows from sheet %r", len(df), sheet_title)
        return df

    def extract_to_lake(self) -> Path:
        """Dump the raw roster, completely untouched, into the local data lake.

        Writes a Parquet snapshot to `data/raw/google_sheets/<YYYY-MM-DD>/roster.parquet`.
        """
        df = self.fetch_raw_roster()

        snapshot_dir = LAKE_RAW_DIR / "google_sheets" / date.today().isoformat()
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        out_path = snapshot_dir / "roster.parquet"

        df.to_parquet(out_path, index=False)
        logger.info("Saved raw roster snapshot -> %s (%d rows)", out_path, len(df))
        return out_path


if __name__ == "__main__":
    configure_logging()
    extractor = GoogleSheetsExtractor()

    print("Testing Google Sheets connection...")
    ok = extractor.test_connection()
    print(f"Connection status: {'OK' if ok else 'FAILED'}")

    if ok:
        print("\nExtracting raw roster snapshot to the data lake...")
        lake_path = extractor.extract_to_lake()
        print(f"  roster -> {lake_path}")
