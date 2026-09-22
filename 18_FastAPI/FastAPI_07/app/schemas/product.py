# app/schemas/product.py


from typing import Literal
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):

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


class ProductResponse(BaseModel):
    id: int
    name: str
    price: int
    category: str
    quantity: int


class ProductListResponse(BaseModel):
    count: int
    products: list[ProductResponse]


class MessageResponse(BaseModel):
    message: str