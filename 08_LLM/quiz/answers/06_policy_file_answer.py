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
    / "nextlab_operation_policy.txt"
)

if not FILE_PATH.exists():
    raise FileNotFoundError(
        f"파일을 찾을 수 없습니다: {FILE_PATH}"
    )

uploaded_file = client.files.upload(
    file=str(FILE_PATH)
)

print("=" * 80)
print("1. 업로드 정보")
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

file_info = client.files.get(
    name=uploaded_file.name
)

print("\n" + "=" * 80)
print("2. Metadata")
print("=" * 80)

print(
    file_info
)

prompt_1 = """
첨부된 운영정책을 읽고
다음 항목을 정리해줘.

1. 출석 규칙
2. 평가 규칙
3. 프로젝트 규칙
4. API Key 관리 규칙
5. 생성형 AI 사용 규칙

문서에 없는 내용은
추측하지 마.
"""

interaction_1 = client.interactions.create(
    model=MODEL_NAME,
    input=[
        {
            "type": "text",
            "text": prompt_1,
        },
        {
            "type": "document",
            "uri": uploaded_file.uri,
            "mime_type": uploaded_file.mime_type,
        },
    ],
)

print("\n" + "=" * 80)
print("3. 첫 번째 질문")
print("=" * 80)

print(
    interaction_1.output_text
)

prompt_2 = """
정책 문서를 기준으로 답해줘.

1. 출석률 79%이면 정상 수료 조건을 만족하는가?
2. 총점 85점, 실습평가 35점이면 추가 조치가 필요한가?
3. 프로젝트 팀을 5명으로 구성해도 되는가?
4. API Key를 Python 코드 안에 적어도 되는가?
5. 같은 파일에 다시 질문할 때 반드시 재업로드해야 하는가?

각 답은 아래 형식으로 작성해줘.

결론:
근거 규칙:

문서에 없는 내용을
추측해서 추가하지 마.
"""

interaction_2 = client.interactions.create(
    model=MODEL_NAME,
    input=[
        {
            "type": "text",
            "text": prompt_2,
        },
        {
            "type": "document",
            "uri": uploaded_file.uri,
            "mime_type": uploaded_file.mime_type,
        },
    ],
)

print("\n" + "=" * 80)
print("4. 두 번째 질문")
print("=" * 80)

print(
    interaction_2.output_text
)

client.files.delete(
    name=uploaded_file.name
)

print(
    "\n업로드한 파일을 삭제했습니다."
)
