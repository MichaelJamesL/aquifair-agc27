from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_prefix="NERACA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "NERACA API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://neraca:neraca@localhost:55432/neraca"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])
    data_dir: Path = Path(__file__).resolve().parents[3] / "data"
    auto_create_tables: bool = False
    docs_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
