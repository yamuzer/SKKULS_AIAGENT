from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

app = FastAPI()

class UserCreate(BaseModel):

    username: str = Field(
        min_length=3, 
        max_length=20
    )

    password: str = Field(
        min_length=8,
        max_length=30
    )

    email: str


    # username 검증
    @field_validator('username')
    @classmethod
    def validate_username(
        cls,
        value: str
    ):

        value = value.strip()

        if not value:
            raise ValueError(
                'username은 공백일 수 없습니다.'
            )

        if value.lower() == 'admin':
            raise ValueError(
                'admin은 사용할 수 없는 이름입니다.'
            )


        return value


    # password 검증
    @field_validator('password')
    @classmethod
    def validate_password(
        cls,
        value: str
    ):

        has_number = any(
            character.isdigit()
            for character in value
        )

        if not has_number:
            raise ValueError(
                'password에는 숫자가 1개 이상 포함되어야 합니다.'
            )

        return value



    # email 검증
    @field_validator('email')
    @classmethod
    def nomalize_email(
        cls,
        value: str
    ) -> str:

        value = value.strip().lower()

        if '@' not in value:
            raise ValueError(
                '올바른 email 형식이 아닙니다.'
            )

        return value



class UserResponse(BaseModel):
    username: str

    email: str

    message: str



@app.post(
    '/users',
    response_model=UserResponse
)
def create_user(
    user: UserCreate
):

    return {
        'username': user.user.username,
        'email': user.email,
        'message': '회원가입이 완료되었습니다.'
    }
