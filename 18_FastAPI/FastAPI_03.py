from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

'''
{
    'name': 'Lapto',
    'price': 1500000,
    'description': '수업용 노트북',
    'in_stock': true
}
'''

class Product(BaseModel):

    name: str
    price: int
    category: str

    description: str | None = None

    in_stock: bool = True



class ProductSummaryResponse(BaseModel):
    name: str
    price: int
    category: str
    message: str



@app.get('/')
def root():
    return {
        'message': 'root입니다.'
    }


@app.post('/products')
def create_product(
    product: Product
):

    return {
        'message': '제품이 생산되었습니다.',
        'product': product
    }


@app.post('/products/summary')
def create_product_summary(
    product: Product
):

    return {
        '이름': product.name,
        '가격': product.price,
        '카테고리': product.category,
        '메세지': (
            f'{product.name} 제품은 {product.category} 카테고리이며 '
            f'가격은 {product.price}원입니다.'
        )
    }


@app.post(
        '/products/summary2',
        response_model=ProductSummaryResponse
)
def create_product_summary_response(
    product: Product
):
    return {
        'name': product.name,
        'price': product.price,
        'category': product.category,
        'message': (
            f'{product.name} 제품은 {product.category} 카테고리이며 '
            f'가격은 {product.price}원입니다.'
        )
    }


class AgentRequest(BaseModel):
    user_id: str

    thread_id: str

    message: str

    use_memory: bool = True


@app.post('/agent/chat')
def agent_chat(
    request: AgentRequest
):

    return {
        'user_id': request.user_id,
        'thread_id': request.thread_id,
        'question': request.message,
        'use_memory': request.use_memory,
        'answer': 'agent 답입니다.',
    }

