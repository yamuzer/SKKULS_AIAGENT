from pydantic import BaseModel, Field, field_validator

class AgentRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=5000
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


class AgentResponse(BaseModel):
    answer: str
    used_tools: list[str]


