from fastapi import FastAPI
from app.routers import health, external_api
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

app.include_router(health.router)
app.include_router(external_api.router)

@app.get(
    '/',
    tags=['Root']
)
def root():
    return {
        'message':'External API Ex',
        'version': settings.app_version,
        'environment': settings.environment,
        'docs':'/docs',
        'health': '/health',
        'single_external_call': '/external/posts/1'
    }
