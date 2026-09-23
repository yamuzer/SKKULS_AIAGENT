from pydantic import BaseModel, Field, field_validator

class ChatRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=10000
    )

    system_prompt: str | None = Field(
        default='당신은 친절하고 정확하게 설명하는 AI 인스턴스입니다.',
        max_length=3000
    )

    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0
    )

    @field_validator('message')
    @classmethod
    def validate_message(
        cls,
        value: str
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                '질문은 공백일 수 없습니다.'
            )

        return value


class ChatResponse(BaseModel):
    model: str
    answer: str


class ModelInfoResponse(BaseModel):
    model: str
    api_key_configured: bool

