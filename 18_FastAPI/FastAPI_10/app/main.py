from fastapi import FastAPI
from app.routers import health, products, config, dependency_demo
from app.core.config import get_settings

settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

app.include_router(health.router)
app.include_router(products.router)
app.include_router(config.router)
app.include_router(dependency_demo.router)

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
        'config': '/config',
        'dependency_demo': '/dependency-demo'
    }
