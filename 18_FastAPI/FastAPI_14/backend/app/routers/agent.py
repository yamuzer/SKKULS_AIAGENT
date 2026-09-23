from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.dependencies import AgentServiceDep

from app.schemas.agent import AgentRequest, AgentResponse


router = APIRouter(
    prefix='/api/agent',
    tags=['LangGraph Agent']
)


@router.post(
    "",
    response_model=AgentResponse
)
async def invoke_agent(
    request: AgentRequest,
    service: AgentServiceDep
):

    answer, used_tools = await service.invoke(request.message)


    return {
        'answer': answer,
        'used_tools': used_tools
    }


@router.post(
    '/stream',
    response_class=StreamingResponse
)
async def stream_agent(
    request: AgentRequest,
    service: AgentServiceDep
): 
    async def generator():
        async for text in service.stream(request.message):
            yield text


    return StreamingResponse(
        generator(),
        media_type='text/plain; charset=utf-8'
    )