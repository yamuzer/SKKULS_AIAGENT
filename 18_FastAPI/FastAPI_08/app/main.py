from fastapi import FastAPI
from app.routers import health, products

app = FastAPI()

app.include_router(health.router)
app.include_router(products.router)

@app.get(
    '/',
    tags=['Root']
)
def root():
    return {
        'message': 'root',
        'docs':'/docs',
        'health': '/health'
    }
