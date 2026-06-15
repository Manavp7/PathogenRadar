from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the demo API."""

    model_config = SettingsConfigDict(env_prefix="PATHOGENRADAR_", env_file=".env")

    app_name: str = "PathogenRadar API"
    environment: str = "demo"
    version: str = "0.1.0"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    require_api_key: bool = False
    demo_api_key: str = "pathogenradar-demo"


@lru_cache
def get_settings() -> Settings:
    return Settings()
