from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import agent, health

app = FastAPI(
    title=settings.app_name,
    version='1.0.0'
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin
    ],
    allow_credentials=True,
    allow_methods=[
        'GET',
        'POST',
        'OPTIONS'
    ],
    allow_headers=[
        'Content-Type'
    ]
)

app.include_router(health.router)
app.include_router(agent.router)



@app.get(
    '/',
    tags=['Root']
)
def root():
    return {
        'message': 'FastAPI + React + LangGraph Agent',
        'agent_api': '/api/agent',
        'stream_api': '/api/agent/stream',
        'docs': '/docs'
    }