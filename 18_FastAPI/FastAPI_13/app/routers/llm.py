from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.core.dependencies import GeminiServiceDep
from app.schemas.llm import ChatRequest, ChatResponse, ModelInfoResponse
from app.services.gemini_service import GeminiAPIError, GeminiConfigurationError



router = APIRouter(
    prefix='/llm',
    tags=['LLM']
)


@router.get(
    '/model',
    response_model=ModelInfoResponse
)
def get_model_info(
    service: GeminiServiceDep
):
    return {
        'model': service.model,
        'api_key_configured': bool(service.api_key)
    }


@router.post(
    '/chat',
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest,
    service: GeminiServiceDep
):
    try:
        answer = await service.generate(request)

        return {
            'model': service.model,
            'answer': answer
        }

    except GeminiConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        )from error

    except GeminiAPIError as error:
        http_status = (
            status.HTTP_429_TOO_MANY_REQUESTS
            if error.code == 429
            else status.HTTP_502_BAD_GATEWAY
        )

        raise HTTPException(
            status_code=http_status,
            detail={
                'message': 'Gemini API 호출에 실패했습니다.',
                'gemini_status': error.code,
                'gemini_message': error.message
            }
        ) from error


@router.post(
        '/stream',
        response_class=StreamingResponse
)
async def stream_chat(
        request: ChatRequest,
        service: GeminiServiceDep
):

    try:
        service.ensure_configured()

    except GeminiConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        ) from error


    async def generate():
        try:
            async for text in service.stream(request):
                yield text

        except GeminiAPIError as error:
            yield f'\n\n[Gemini API 오류] {error.message}'

    return StreamingResponse(
        generate(),
        media_type='text/plain; charset=utf-8'
    )