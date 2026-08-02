"""Strongly-typed application configuration, loaded from environment variables / .env.

Usage:
    from config.settings import get_settings

    settings = get_settings()
    engine = create_engine(settings.postgres_uri)
"""
from __future__ import annotations

import logging
import logging.handlers
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    GDRIVE_CREDENTIALS_FILE: Path

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


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()


def configure_logging(settings: Settings | None = None) -> logging.Logger:
    """Initialize root logging (console + rotating file handler) from Settings.

    Idempotent: safe to call multiple times without duplicating handlers.
    """
    settings = settings or get_settings()
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
