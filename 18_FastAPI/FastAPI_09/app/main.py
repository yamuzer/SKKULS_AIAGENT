from fastapi import FastAPI
from app.routers import health, products, config
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

app.include_router(health.router)
app.include_router(products.router)
app.include_router(config.router)

@app.get(
    '/',
    tags=['Root']
)
def root():
    return {
        'message': settings.app_name,
        'version': settings.app_version,
        'environment': settings.environment,
        'docs':'/docs',
        'health': '/health',
        'config': '/config'
    }
