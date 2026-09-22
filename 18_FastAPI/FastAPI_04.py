from typing import Literal
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI()


class Product(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=50
    )

    price: int = Field(
        gt=0,
        le=100_000_000
    )

    category: Literal[
        'computer',
        'book',
        'education'
    ]


    quantity: int = Field(
        default=1,
        ge=0,
        le=1000
    )

    in_stock: bool = True


products = [
    {
        'id': 1,
        'name': 'Laptop',
        'price': 1500000,
        'category': 'computer',
        'quantity': 10,
        'in_stock': True
    },
    
    {
        'id': 2,
        'name': 'Keyboard',
        'price': 80000,
        'category': 'computer',
        'quantity': 30,
        'in_stock': True
    },

    {
        'id': 3,
        'name': 'FastAPI book',
        'price': 42000,
        'category': 'book',
        'quantity': 20,
        'in_stock': True
    },

    {
        'id': 4,
        'name': 'AI Course',
        'price': 1200000,
        'category': 'education',
        'quantity': 15,
        'in_stock': True
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
        product[id]
        for product in products
    )

    return max_id + 1


@app.get('/')
def root():
    return {
        'message': 'root임'
    }


# Create

@app.post(
    '/products',
    status_code=status.HTTP_201_CREATED
)
def create_product(product: Product):
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


# Read

@app.get('/products')
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


@app.get('/products/{product_id}')
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


# Update

@app.put('/products/{product_id}')
def update_product(
    product_id: int,
    product: Product
):
    stored_product = find_product(product_id)

    # 404
    if stored_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='수정할 제품을 찾을 수 없습니다.'
        )

    update_data = product.model_dump()

    stored_product.clear()

    stored_product.update(
        {
            'id': product_id,
            **update_data
        }
    )

    return {
        'message': '제품이 수정되었습니다.',
        'product': stored_product
    }


# Delete

@app.delete('/products/{product_id}')
def delete_product(
    product_id: int
):
    product = find_product(product_id)

    # 404
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='삭제할 제품을 찾을 수 없습니다.'
        )

    products.remove(product)

    return {
        'message': '제품이 삭제되었습니다.',
        'delete_product': product
    }