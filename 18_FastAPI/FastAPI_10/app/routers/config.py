from fastapi import APIRouter

from app.core.config import settings
from app.schemas.config import PublicConfigResponse

router = APIRouter(
    prefix='/config',
    tags=['Config']
)

@router.get(
    '',
    response_model=PublicConfigResponse
)
def get_public_config():
    return {
        'app_name': settings.app_name,
        'app_version': settings.app_version,
        'app_host': settings.app_host,
        'app_port': settings.app_port,
        'debug': settings.debug,
        'environment': settings.environment,
        'gemini_model': settings.gemini_model,
        'has_gemini_api_key': bool(settings.gemini_api_key)
    }