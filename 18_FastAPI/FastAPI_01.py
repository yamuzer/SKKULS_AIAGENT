from fastapi import FastAPI

app = FastAPI()


@app.get('/')
def root():
    return {
        'message': 'Hello fastAPI',
        'status': 'success'
    }


@app.get('/hello')
def hello():
    return {
        'message': 'FastAPI ex1입니다. hello 함수 실행'
    }



@app.get('/agent')
def agent():
    return {
        'message': '나중에 이 위치에 Agent를 연결',
        'agent_ready': False
    }


@app.get('/users/{user_id}')
def get_user(
    user_id: int
):

    return {
        'user_id': user_id,
        'message': f'{user_id}번 사용자입니다.'
    }


@app.get('/users/{user_id}/orders/{order_id}')
def get_user_order(
    user_id: int,
    order_id: int
):
    return{
        'user_id': user_id,
        'order_id': order_id,
        'message': f'{user_id}번 사용자의 {order_id}번 주문입니다.'
    }