from fastapi import APIRouter, HTTPException, status

from app.schemas.product import (
MessageResponse, 
ProductResponse,
ProductCreate,
ProductListResponse
)

from app.services import product_service


router = APIRouter(
    prefix='/products',
    tags=['Products']
)



# 제품 목록

@router.get(
    '',
    response_model=ProductListResponse
)
def get_products(
    category: str | None = None,
    limit: int = 2
):

    products = product_service.list_products(
        category=category,
        limit=limit
    )

    return {
        'count': len(products),
        'products': products
    }



# 제품 하나 조회
@router.get(
    '/{product_id}',
    response_model=ProductResponse
)
def get_product(product_id: int):

    product = product_service.get_product(product_id)

    # 404
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='제품을 찾을 수 없습니다.'
        )

    return product


# 제품 생성
@router.post(
    '',
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(product: ProductCreate):
    try:
        return product_service.create_product(product)

    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err)
        )from err


@router.put(
    '/{product_id}',
    response_model=ProductResponse
)
def update_product(
    product_id: int,
    product: ProductCreate
):
    try:
        updated_product = product_service.update_product(
            product_id=product_id,
            product=product
        )

    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err)
        )from err

    if updated_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='수정할 제품을 찾을 수 없습니다.'
        )

    return updated_product


@router.delete(
    '/{product_id}',
    response_model=MessageResponse
)
def delete_product(product_id: int):
    deleted = product_service.delete_product(product_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='삭제할 제품을 찾을 수가 없습니다.'
        )

    return {
        'message': f'{product_id}번 제품이 삭제되었습니다.'
    }
    