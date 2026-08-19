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

IMAGE_PATH = (
    DATA_DIR
    / "digital_lab_scene.png"
)

if not IMAGE_PATH.exists():
    raise FileNotFoundError(
        f"이미지를 찾을 수 없습니다: {IMAGE_PATH}"
    )

uploaded_image = client.files.upload(
    file=str(IMAGE_PATH)
)

print("=" * 80)
print("1. 이미지 업로드")
print("=" * 80)

print(
    "name:",
    uploaded_image.name,
)

print(
    "uri:",
    uploaded_image.uri,
)

print(
    "mime_type:",
    uploaded_image.mime_type,
)

prompt = """
첨부된 교육실 이미지를 관찰하고
이미지에서 직접 확인되는 내용만 분석해줘.

다음 순서로 답해줘.

1. 전체 장면
2. 보이는 사람 수
3. PC 또는 책상 영역 수
4. 읽을 수 있는 텍스트
5. HELP DESK 위치
6. EXIT 위치
7. CABLE AREA가 통행에 영향을 줄 가능성
8. 이미지에서만으로 확정할 수 없는 사항

규칙:

- 사람의 이름이나 신원을 추측하지 마.
- 보이지 않는 사고 원인을 만들어내지 마.
- 정확히 판단하기 어려우면 "확인 어려움"이라고 적어줘.
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
)

print("\n" + "=" * 80)
print("2. 이미지 분석 결과")
print("=" * 80)

print(
    interaction.output_text
)

print("\n" + "=" * 80)
print("3. Token Usage")
print("=" * 80)

if interaction.usage:
    print(
        "Input:",
        interaction.usage.total_input_tokens,
    )

    print(
        "Output:",
        interaction.usage.total_output_tokens,
    )

    print(
        "Thought:",
        interaction.usage.total_thought_tokens,
    )

    print(
        "Total:",
        interaction.usage.total_tokens,
    )

client.files.delete(
    name=uploaded_image.name
)

print(
    "\n업로드한 이미지를 삭제했습니다."
)
