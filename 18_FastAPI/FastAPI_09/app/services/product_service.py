from app.schemas.product import ProductCreate


_products: list[dict] = [
    {
        'id': 1,
        'name': 'Laptop',
        'price': 1_500_000,
        'category': 'computer',
        'quantity': 10
    },
    
    {
        'id': 2,
        'name': 'Keyboard',
        'price': 80_000,
        'category': 'computer',
        'quantity': 30
    },

    {
        'id': 3,
        'name': 'FastAPI book',
        'price': 42_000,
        'category': 'book',
        'quantity': 20
    },

    {
        'id': 4,
        'name': 'AI Course',
        'price': 1_200_000,
        'category': 'education',
        'quantity': 15
    }

]


def _get_next_id() -> int:
    if not _products:
        return 1

    max_id = max(
        product['id']
        for product in _products
    )

    return max_id + 1

def _normalize_name(name: str) -> str:

    return name.strip().lower()



def list_products(
    category: str | None = None,
    limit: int = 2
) ->list[dict]:

    result = _products.copy()

    if category is not None:
        result = [
            product
            for product in result
            if product['category'] == category
        ]

    return result[: limit]



def get_product(product_id: int) -> dict | None:

    for product in _products:
        if product['id'] == product_id:
            return product

    return None



def create_product(product: ProductCreate) -> dict:

    normalized_name = _normalize_name(product.name)

    for stored_product in _products:
        if _normalize_name(stored_product['name']) == normalized_name:
            raise ValueError(
                '같은 이름의 제품이 이미 존재합니다.'
            )

    new_product = {
        'id': _get_next_id(),
        **product.model_dump()
    }

    _products.append(new_product)

    return new_product



def update_product(
        product_id: int,
        product: ProductCreate
) -> dict | None:

    stored_product = get_product(product_id)

    if stored_product is None:
        return None


    normalized_name = _normalize_name(product.name)

    for other_product in _products:
        if (
            other_product['id'] != product_id
            and
            _normalize_name(other_product['name']) == normalized_name
        ):
            raise ValueError(
                '같은 이름의 다른 제품이 이미 존재합니다.'
            )

        stored_product.clear()
        stored_product.update(
            {
                'id': product_id,
                **product.model_dump()
            }
        )

        return stored_product
    


def delete_product(product_id: int) -> bool:

    product = get_product(product_id)

    if product is None:
        return False

    _products.remove(product)

    return True
