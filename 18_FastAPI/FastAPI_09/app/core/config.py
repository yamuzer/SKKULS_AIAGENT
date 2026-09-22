from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "FastAPI Config Ex"
    app_version: str = "1.0.0"

    app_host: str = "127.0.0.1"

    app_port: int = Field(
        default=8000,
        ge=1,
        le=65535
    )

    debug: bool = True

    environment: Literal[
        'development',
        'test',
        'productions'
    ] = "development"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.7-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()