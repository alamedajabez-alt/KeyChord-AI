"""Central configuration. Every tunable comes from environment variables (prefix KEYCHORD_)."""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KEYCHORD_", env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+psycopg://keychord:keychord@localhost:5432/keychord"

    storage_backend: str = "local"  # "local" now; "s3" later behind the same interface
    storage_root: Path = Path("./storage_data")

    cors_origins: str = "http://localhost:5173"

    max_upload_mb: int = Field(default=50, ge=1)
    max_duration_seconds: int = Field(default=600, ge=10)
    analysis_timeout_seconds: int = Field(default=900, ge=30)

    auth_enabled: bool = False
    secret_key: str = "change-me"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
