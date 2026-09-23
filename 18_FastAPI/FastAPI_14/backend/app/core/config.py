from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = 'FastAPI React LangGraph Agent Ex'
    app_host: str = '127.0.0.1'
    app_port: int = 8000
    debug: bool = True

    frontend_origin: str = 'http://localhost:5173'

    gemini_api_key: str | None = None
    gemini_model: str = 'gemini-3.7-flash'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()