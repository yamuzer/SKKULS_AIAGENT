from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import ExternalApiServiceDep
from app.schemas.external_api import (
    BatchPostRequest,
    BatchPostResponse,
    ExternalPostCreate,
    ExternalPostCreateResponse,
    ExternalPostResponse,
    TimeoutDemoResponse
)

from app.services.external_api_service import (
    ExternalApiConnectionError,
    ExternalApiStatusError,
    ExternalApiTimeoutError
)

router = APIRouter(
    prefix='/external',
    tags=['External API']
)


def convert_external_error(exc: Exception) -> HTTPException:

    if isinstance(exc, ExternalApiTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc)
        )

    if isinstance(exc, ExternalApiStatusError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                'message':str(exc),
                'external_status_code': exc.status_code
            }
        )

    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(exc)
    )



@router.get(
    '/posts/{post_id}',
    response_model=ExternalPostResponse
)
async def get_external_post(
    post_id: int, 
    service: ExternalApiServiceDep
):
    try:
        return await service.get_post(post_id)
    except (
        ExternalApiTimeoutError,
        ExternalApiConnectionError,
        ExternalApiStatusError
    ) as error:
        raise convert_external_error(error) from error


@router.post(
    '/posts',
    response_model=ExternalPostCreateResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_external_post(
    request: ExternalPostCreate,
    service: ExternalApiServiceDep
):
    try:
        return await service.create_post(
            request.model_dump()
        )
    except (
        ExternalApiTimeoutError,
        ExternalApiConnectionError,
        ExternalApiStatusError
    ) as error:
        raise convert_external_error(error) from error


@router.post(
    '/posts/batch',
    response_model=BatchPostResponse
)
async def get_external_posts_batch(
    request: BatchPostRequest,
    service: ExternalApiServiceDep
):
    try:
        posts = await service.get_posts_concurrently(
            request.post_ids
        )

        return {
            'count': len(posts),
            'posts': posts
        }

    except (
        ExternalApiTimeoutError,
        ExternalApiConnectionError,
        ExternalApiStatusError
    ) as error:
        raise convert_external_error(error) from error


@router.get(
    '/timeout-demo',
    response_model=TimeoutDemoResponse
)
async def timeout_demo(
    service: ExternalApiServiceDep,
    delay_seconds: float = Query(
        default=2.0,
        ge=0.0,
        le=10.0
    ),
    timeout_seconds: float = Query(
        default=1.0,
        gt=0.0,
        le=10.0
    )
):
    try:
        return await service.timeout_demo(
            delay_seconds=delay_seconds,
            timeout_seconds=timeout_seconds
        )
    except (
        ExternalApiTimeoutError,
        ExternalApiConnectionError,
        ExternalApiStatusError
    ) as error:
        raise convert_external_error(error) from error