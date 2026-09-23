from typing import Annotated
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.gemini_service import GeminiService


SettingsDep = Annotated[
    Settings,
    Depends(get_settings)
]


def get_gemini_service(
        settings: SettingsDep
) -> GeminiService:

    return GeminiService(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        default_temperature=settings.gemini_temperature
    )


GeminiServiceDep = Annotated[
    GeminiService,
    Depends(get_gemini_service)
]