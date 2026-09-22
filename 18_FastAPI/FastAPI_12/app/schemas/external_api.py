from pydantic import BaseModel, Field

class ExternalPostResponse(BaseModel):
    userId: int
    id: int
    title: str
    body: str


class ExternalPostCreate(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=200
    )

    body: str = Field(
        min_length=1,
        max_length=2000
    )

    user_id: int = Field(
        ge=1
    )


class ExternalPostCreateResponse(BaseModel):
    title: str
    body: str
    user_id: int
    id: int

class BatchPostRequest(BaseModel):
    post_ids: list[int] = Field(
        min_length=1,
            max_length=10
        )

class BatchPostResponse(BaseModel):
    count: int
    posts: list[ExternalPostResponse]


class TimeoutDemoResponse(BaseModel):
    delay_seconds: float
    timeout_seconds: float
    message: str