from fastapi import FastAPI

from app.core.config import settings
from app.routers import health, llm

app = FastAPI(
    title=settings.app_name
)

app.include_router(health.router)
app.include_router(llm.router)


@app.get(
        '/',
        tags=['Root']
)
def root():
    return {
       'message': 'fastAPI + LLM',
       'docs': '/docs',
       'chat': '/llm/chat',
       'stream':
       '/llm/stream' 
    }