import httpx

from functools import lru_cache
from typing import Annotated, AsyncIterator
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.external_api_service import ExternalApiService


SettingsDep = Annotated[
    Settings,
    Depends(get_settings)
]

async def get_external_api_service(
        settings: SettingsDep
) -> AsyncIterator[ExternalApiService]:

    timeout = httpx.Timeout(
        settings.external_api_timeout
    )

    async with httpx.AsyncClient(timeout= timeout) as client:
        yield ExternalApiService(
            client=client,
            base_url=settings.external_api_base_url,
            delay_base_url=settings.delay_api_base_url
        )


ExternalApiServiceDep = Annotated[
    ExternalApiService,
    Depends(get_external_api_service)
]
