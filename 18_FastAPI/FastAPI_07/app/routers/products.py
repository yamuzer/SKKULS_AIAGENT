from fastapi import APIRouter, HTTPException, status

from app.schemas.product import (
MessageResponse, 
ProductResponse,
ProductCreate,
ProductListResponse
)


router = APIRouter(
    prefix='/products',
    tags=['Products']
)

products = [
    {
        'id': 1,
        'name': 'Laptop',
        'price': 1500000,
        'category': 'computer',
        'quantity': 10
    },
    
    {
        'id': 2,
        'name': 'Keyboard',
        'price': 80000,
        'category': 'computer',
        'quantity': 30
    },

    {
        'id': 3,
        'name': 'FastAPI book',
        'price': 42000,
        'category': 'book',
        'quantity': 20
    },

    {
        'id': 4,
        'name': 'AI Course',
        'price': 1200000,
        'category': 'education',
        'quantity': 15
    }

]


def find_product(product_id: int):

    for product in products:
        if product['id'] == product_id:
            return product

    return None

def get_next_product_id():
    if not products:
        return 1

    max_id = max(
        product['id']
        for product in products
    )

    return max_id + 1


@router.get(
    '',
    response_model=ProductListResponse
)
def get_products(
    category: str | None = None,
    limit: int = 2
):

    result = products.copy()

    if category is not None:
        result = [
            product
            for product in result
            if product['category'] == category
        ]


    result = result[: limit]

    return {
        'count': len(result),
        'products': result
    }



@router.get(
    '/{product_id}',
    response_model=ProductResponse
)
def get_product(product_id: int):

    product = find_product(product_id)

    # 404
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='제품을 찾을 수 없습니다.'
        )

    return {
        'product': product
    }

@router.post(
    '',
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(product: ProductCreate):
    new_id = get_next_product_id()

    new_product = {
        'id': new_id,
        **product.model_dump()
    }

    products.append(new_product)

    return {
        'message': '제품이 생성되었습니다.',
        'product': new_product
    }