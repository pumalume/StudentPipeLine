"""Strongly-typed application configuration, loaded from environment variables / .env.

Usage:
    from config.settings import get_settings

    settings = get_settings()
    engine = create_engine(settings.postgres_uri)
"""
from __future__ import annotations

import logging
import logging.handlers
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Branches and datasets the pipeline pulls from. To add a branch, add its name
# here and the matching GSHEET_<BRANCH>_<DATASET>_ID / _TAB fields to Settings.
SHEET_BRANCHES: tuple[str, ...] = ("golcuk", "izmit")
SHEET_DATASETS: tuple[str, ...] = ("masterlist", "enrollment")


@dataclass(frozen=True)
class SheetSource:
    """One Google Sheet to extract: a single dataset for a single branch."""

    branch: str
    dataset: Literal["masterlist", "enrollment"]
    spreadsheet_id: str
    tab: str = ""  # empty -> use the spreadsheet's first tab

    @property
    def key(self) -> str:
        """Stable identifier used for logging and data lake paths."""
        return f"{self.branch}/{self.dataset}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FILE: Path = Path("data/logs/pipeline.log")
    BATCH_SIZE: int = Field(default=1000, gt=0)

    # --- WordPress source (MySQL / MariaDB) ---
    WP_DB_HOST: str
    WP_DB_PORT: int = 3306
    WP_DB_NAME: str
    WP_DB_USER: str
    WP_DB_PASSWORD: str

    # --- Target database (PostgreSQL) ---
    PG_DB_HOST: str
    PG_DB_PORT: int = 5432
    PG_DB_NAME: str
    PG_DB_SCHEMA: str = "SchoolRegistration"
    PG_DB_USER: str
    PG_DB_PASSWORD: str

    # --- File / API paths ---
    DATA_INPUT_DIR: Path = Path("data/input")
    GOOGLE_CREDENTIALS_FILE: Path

    # --- Google Sheets sources (one spreadsheet per branch per dataset) ---
    # Leave a *_TAB blank to read the spreadsheet's first tab.
    GSHEET_GOLCUK_MASTERLIST_ID: str = ""
    GSHEET_GOLCUK_MASTERLIST_TAB: str = ""
    GSHEET_GOLCUK_ENROLLMENT_ID: str = ""
    GSHEET_GOLCUK_ENROLLMENT_TAB: str = ""

    GSHEET_IZMIT_MASTERLIST_ID: str = ""
    GSHEET_IZMIT_MASTERLIST_TAB: str = ""
    GSHEET_IZMIT_ENROLLMENT_ID: str = ""
    GSHEET_IZMIT_ENROLLMENT_TAB: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def wordpress_uri(self) -> str:
        """SQLAlchemy connection URI for the WordPress MySQL/MariaDB source."""
        return (
            f"mysql+pymysql://{quote_plus(self.WP_DB_USER)}:{quote_plus(self.WP_DB_PASSWORD)}"
            f"@{self.WP_DB_HOST}:{self.WP_DB_PORT}/{self.WP_DB_NAME}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def postgres_uri(self) -> str:
        """SQLAlchemy connection URI for the target PostgreSQL database."""
        return (
            f"postgresql+psycopg2://{quote_plus(self.PG_DB_USER)}:{quote_plus(self.PG_DB_PASSWORD)}"
            f"@{self.PG_DB_HOST}:{self.PG_DB_PORT}/{self.PG_DB_NAME}"
        )

    @property
    def sheet_sources(self) -> list[SheetSource]:
        """Every configured Google Sheet, one entry per branch/dataset pair.

        Pairs whose `*_ID` is blank are left out — see `missing_sheet_sources`.
        """
        sources: list[SheetSource] = []
        for branch, dataset in _sheet_source_slots():
            spreadsheet_id = self._sheet_field(branch, dataset, "ID")
            if not spreadsheet_id:
                continue
            sources.append(
                SheetSource(
                    branch=branch,
                    dataset=dataset,  # type: ignore[arg-type]
                    spreadsheet_id=spreadsheet_id,
                    tab=self._sheet_field(branch, dataset, "TAB"),
                )
            )
        return sources

    @property
    def missing_sheet_sources(self) -> list[str]:
        """Branch/dataset pairs with no spreadsheet ID configured."""
        return [
            f"{branch}/{dataset}"
            for branch, dataset in _sheet_source_slots()
            if not self._sheet_field(branch, dataset, "ID")
        ]

    def _sheet_field(self, branch: str, dataset: str, suffix: str) -> str:
        return str(getattr(self, f"GSHEET_{branch.upper()}_{dataset.upper()}_{suffix}", "")).strip()


def _sheet_source_slots() -> list[tuple[str, str]]:
    """All branch/dataset combinations the pipeline knows about."""
    return [(branch, dataset) for branch in SHEET_BRANCHES for dataset in SHEET_DATASETS]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()


def configure_console_encoding() -> None:
    """Force stdout/stderr to UTF-8 so Turkish characters don't crash the console.

    Windows terminals default to cp1252, which raises UnicodeEncodeError on names
    like "Gölcük" or a combining dot above. Undecodable output is replaced rather
    than fatal. Idempotent and a no-op on streams that don't support reconfigure.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


def configure_logging(settings: Settings | None = None) -> logging.Logger:
    """Initialize root logging (console + rotating file handler) from Settings.

    Also forces UTF-8 console output. Idempotent: safe to call multiple times
    without duplicating handlers.
    """
    settings = settings or get_settings()
    configure_console_encoding()
    settings.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger("schoolpipe")
