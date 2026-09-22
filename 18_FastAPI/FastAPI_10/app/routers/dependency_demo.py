from typing import Annotated
from fastapi import APIRouter, Depends

from app.core.dependencies import SettingsDep

router = APIRouter(
    prefix='/dependency-demo',
    tags=['Dependency Demo']
)

def build_runtime_info(
        settings: SettingsDep
) -> dict:

    return {
        'app_name': settings.app_name,
        'environment': settings.environment,
        'message': 'Settings가 하위 의존성을 통해 주입되었습니다.'
    }


RuntimInfoDep = Annotated[
    dict,
    Depends(build_runtime_info)
]


@router.get('')
def dependency_demo(
    runtime_info: RuntimInfoDep
):
    return runtime_info