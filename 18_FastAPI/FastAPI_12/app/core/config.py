from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "FastAPI External API Ex"
    app_version: str = "1.0.0"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = True
    environment: str = "development"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.7-flash"

    external_api_base_url: str = "https://jsonplaceholder.typicode.com"
    delay_api_base_url: str = "https://httpbin.org"
    external_api_timeout: float = 5.0

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