from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(
    prefix='/health',
    tags=['Health']
)


@router.get('')
def health_check():
    return {
        'status': 'ok',
        'app_name': settings.app_name,
        'gemini_model': settings.gemini_model,
        'gemini_api_key_configured': bool(settings.gemini_api_key)
    }