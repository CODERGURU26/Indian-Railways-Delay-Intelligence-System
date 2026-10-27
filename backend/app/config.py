from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "indian-railways-delay-intelligence"
    app_env: Literal["development", "production", "test"] = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./railway_delay.db"
    dataset_config: str = "2026-10-10_"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
