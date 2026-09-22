from functools import lru_cache
from typing import Annotated
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.product_service import ProductService

@lru_cache
def get_product_service() -> ProductService:

    return ProductService()

SettingsDep = Annotated[
    Settings,
    Depends(get_settings)
]

ProductServiceDep = Annotated[
    ProductService,
    Depends(get_product_service)
]
