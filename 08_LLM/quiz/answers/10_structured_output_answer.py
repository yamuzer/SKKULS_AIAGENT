import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"

load_dotenv(
    dotenv_path=ENV_PATH
)

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY를 읽을 수 없습니다."
    )

client = genai.Client(
    api_key=api_key
)

MODEL_NAME = "gemini-3.7-flash"

from pydantic import BaseModel, Field


class ClassRow(BaseModel):

    no: int = Field(
        description="NO 열의 번호"
    )

    room: str = Field(
        description="ROOM 열 값"
    )

    time: str = Field(
        description="TIME 열 값"
    )

    subject: str = Field(
        description="SUBJECT 열 값"
    )

    status: str = Field(
        description="STATUS 열 값"
    )


class ClassBoard(BaseModel):

    document_title: str = Field(
        description="이미지 위쪽의 문서 제목"
    )

    rows: list[ClassRow] = Field(
        description="표의 18개 행"
    )

    check_count: int = Field(
        description="STATUS가 CHECK인 행 개수"
    )

    hold_count: int = Field(
        description="STATUS가 HOLD인 행 개수"
    )


IMAGE_PATH = (
    DATA_DIR
    / "class_operation_board.png"
)

if not IMAGE_PATH.exists():
    raise FileNotFoundError(
        f"이미지를 찾을 수 없습니다: {IMAGE_PATH}"
    )

uploaded_image = client.files.upload(
    file=str(IMAGE_PATH)
)

prompt = """
첨부된 이미지는
NEXTLAB CLASS OPERATION BOARD다.

표를 읽어서
구조화된 데이터로 추출해줘.

[추출 열]

- NO
- ROOM
- TIME
- SUBJECT
- STATUS

[규칙]

1. NO 1번부터 18번까지 모두 추출한다.
2. 각 행의 값을 다른 행과 섞지 않는다.
3. document_title에는 이미지 제목을 기록한다.
4. check_count에는 STATUS가 CHECK인 행 개수를 기록한다.
5. hold_count에는 STATUS가 HOLD인 행 개수를 기록한다.
6. 이미지에서 직접 읽은 값만 사용한다.
"""

interaction = client.interactions.create(
    model=MODEL_NAME,
    input=[
        {
            "type": "text",
            "text": prompt,
        },
        {
            "type": "image",
            "uri": uploaded_image.uri,
            "mime_type": uploaded_image.mime_type,
        },
    ],
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": ClassBoard.model_json_schema(),
    },
)

print("=" * 80)
print("1. Gemini 원본 JSON")
print("=" * 80)

print(
    interaction.output_text
)

result = ClassBoard.model_validate_json(
    interaction.output_text
)

print("\n" + "=" * 80)
print("2. Pydantic 검증 결과")
print("=" * 80)

print(
    "문서 제목:",
    result.document_title,
)

for row in result.rows:
    print(
        f"{row.no:>2} | "
        f"{row.room:<4} | "
        f"{row.time} | "
        f"{row.subject:<7} | "
        f"{row.status}"
    )

python_check_count = sum(
    1
    for row in result.rows
    if row.status == "CHECK"
)

python_hold_count = sum(
    1
    for row in result.rows
    if row.status == "HOLD"
)

print("\n" + "=" * 80)
print("3. 개수 검증")
print("=" * 80)

print(
    "Gemini check_count:",
    result.check_count,
)

print(
    "Python CHECK count:",
    python_check_count,
)

print(
    "Gemini hold_count:",
    result.hold_count,
)

print(
    "Python HOLD count:",
    python_hold_count,
)

print(
    "CHECK 일치:",
    result.check_count == python_check_count,
)

print(
    "HOLD 일치:",
    result.hold_count == python_hold_count,
)

client.files.delete(
    name=uploaded_image.name
)

print(
    "\n업로드한 이미지를 삭제했습니다."
)
