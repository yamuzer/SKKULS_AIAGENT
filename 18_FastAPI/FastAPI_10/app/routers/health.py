from fastapi import APIRouter
from app.core.dependencies import SettingsDep

router = APIRouter(
    prefix='/health',
    tags=['Health']
)


@router.get('')
def health_check(
    settings: SettingsDep
):

    return {
        'status': 'ok',
        'message': 'server is running',
        'app_name': settings.app_name,
        'environment': settings.environment
    }