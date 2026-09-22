from fastapi import FastAPI

app = FastAPI()

products = [
    {
        'id': 1,
        'name': 'Laptop',
        'category': 'computer',
        'price': 1500000,
        'in_stock': True
    },
    {
        'id': 1,
        'name': 'Laptop',
        'category': 'computer',
        'price': 1500000,
        'in_stock': True
    },
    {
        'id': 2,
        'name': 'Keyboard',
        'category': 'computer',
        'price': 80000,
        'in_stock': True
    },
    {
        'id': 3,
        'name': 'Mouse',
        'category': 'computer',
        'price': 50000,
        'in_stock': False
    },
    {
        'id': 4,
        'name': 'python basic book',
        'category': 'book',
        'price': 35000,
        'in_stock': True
    },
    {
        'id': 5,
        'name': 'FastAPI basic book',
        'category': 'book',
        'price': 42000,
        'in_stock': True
    },
    {
        'id': 6,
        'name': 'AI Course',
        'category': 'education',
        'price': 1000000,
        'in_stock': True
    },
    {
        'id': 7,
        'name': 'Pandas Course',
        'category': 'education',
        'price': 800000,
        'in_stock': True
    },
]


@app.get('/')
def root():
    return {
        'message': 'root입니다 ~~~~'
    }


@app.get('/hello')
def hello(
    name: str
):
    return {
        '이름': name,
        'message': f'안녕하세요 {name}님~~'
    }


@app.get('/items')
def get_item(
    limit: int = 3
):

    return {
        'limit': limit,
        'items': products[:limit]
    }


@app.get('/search')
def search_product(
    category: str,
    limit: int = 4

):

    filtered_product = [
        product
        for product in products
        if product['category'] == category
    ]

    filtered_product = filtered_product[:limit]

    return {
        'category': category,
        'limit': limit,
        'filtered_count': len(filtered_product),
        'products': filtered_product
    }


@app.get('/stock')
def get_stock(
    available: bool = True
):

    result = [
        product
        for product in products
        if product['in_stock'] == available
    ]

    return {
        '재고': available,
        '갯 수': len(result),
        '해당 물품들': result

    }

@app.get('/filter')
def filter_products(
    category: str | None = None,
    max_price: int | None = None,
    available: bool | None = None,
    limit: int | None = None
):
    result = products.copy()

    if category is not None:
        result = [
            product
            for product in result
            if product['category'] == category
        ]

    if max_price is not None:
        result = [
            product
            for product in result
            if product['price'] <= max_price
        ]


    if available is not None:
        result = [
            product
            for product in result
            if product['in_stock'] == available
        ]

    result = result[:limit]


    return {
        'filters':{
            'category': category,
            'max_price': max_price,
            'available': available,
            'limit': limit
        },
        'count': len(result),
        'products': result
    }