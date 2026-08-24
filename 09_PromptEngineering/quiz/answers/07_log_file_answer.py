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

FILE_PATH = (
    DATA_DIR
    / "support_case_log.txt"
)

if not FILE_PATH.exists():
    raise FileNotFoundError(
        f"파일을 찾을 수 없습니다: {FILE_PATH}"
    )

uploaded_file = client.files.upload(
    file=str(FILE_PATH)
)

print("=" * 80)
print("1. 로그 파일 업로드")
print("=" * 80)

print(
    "name:",
    uploaded_file.name,
)

print(
    "uri:",
    uploaded_file.uri,
)

print(
    "mime_type:",
    uploaded_file.mime_type,
)

prompt = """
첨부된 SUPPORT CASE LOG를 분석해줘.

파일에는 CASE 번호가 있는
교육용 지원 문의 기록이 들어 있다.

다음 순서로 분석해줘.

1. 가장 자주 나타나는 TYPE 후보 3개
2. HIGH LEVEL 사례에서 눈에 띄는 특징
3. RESPONSE_MIN이 큰 CASE 예시 5개
4. REPEAT 값이 큰 CASE 예시
5. 아직 OPEN인 사례에서 확인할 점
6. 데이터만으로 원인이라고 단정할 수 없는 내용

중요:

- 사례를 언급할 때 가능하면 CASE 번호를 함께 적어줘.
- 파일에 없는 CASE를 새로 만들지 마.
- 단순 상관관계를 원인이라고 단정하지 마.
- 정확히 판단하기 어려운 부분은 그렇게 밝혀줘.
"""

interaction = client.interactions.create(
    model=MODEL_NAME,
    input=[
        {
            "type": "text",
            "text": prompt,
        },
        {
            "type": "document",
            "uri": uploaded_file.uri,
            "mime_type": uploaded_file.mime_type,
        },
    ],
)

print("\n" + "=" * 80)
print("2. Gemini 로그 분석")
print("=" * 80)

print(
    interaction.output_text
)

if interaction.usage:

    print("\n" + "=" * 80)
    print("3. Token Usage")
    print("=" * 80)

    print(
        "Input:",
        interaction.usage.total_input_tokens,
    )

    print(
        "Output:",
        interaction.usage.total_output_tokens,
    )

    print(
        "Total:",
        interaction.usage.total_tokens,
    )

client.files.delete(
    name=uploaded_file.name
)

print(
    "\n업로드한 로그 파일을 삭제했습니다."
)
