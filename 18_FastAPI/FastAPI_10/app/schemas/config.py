from pydantic import BaseModel

class PublicConfigResponse(BaseModel):
    app_name: str
    app_version: str
    app_host: str
    app_port: int
    debug: bool
    environment: str
    gemini_model: str
    has_gemini_api_key: bool