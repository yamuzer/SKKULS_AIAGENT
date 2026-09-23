from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings

from app.services.agent_service import AgentService


SettingDep = Annotated[
    Settings,
    Depends(get_settings)
]


@lru_cache
def build_agent(
    api_key: str,
    model_name: str
) -> Any:

    try:
        from app.agent.graph import LangGraphAgent

    except ImportError as error:
        raise RuntimeError(
            'LangGraph 관련 패키지가 설치되어 있지 않습니다.'
        ) from error

    return LangGraphAgent(
        api_key=api_key,
        model_name=model_name
    )


def get_agent_service(
        settings: SettingDep
) -> AgentService:

    api_key = (settings.gemini_api_key or '').strip()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='GEMINI_API_KEY가 설정되 않았습니다.'
        )

    try:
        agent = build_agent(
            api_key=api_key,
            mode_name=settings.gemini_model
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        ) from error

    return AgentService(agent)


AgentServiceDep = Annotated[
    AgentService,
    Depends(get_agent_service)
]