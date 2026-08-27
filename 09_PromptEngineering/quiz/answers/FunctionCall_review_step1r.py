import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.7-flash"


def print_title(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


BRANCH_ENUM = [
    "강남", "여의도", "판교", "광화문", "성수", "잠실",
    "마곡", "구로", "수원", "인천", "대전", "부산",
]

get_room_info_tool = {
    "type": "function",
    "name": "get_room_info",
    "description": (
        "공유오피스 지점과 공간 이름을 입력받아 "
        "해당 공간의 수용 인원, PC 수, 화상회의 가능 여부, "
        "가격 등의 상세 정보를 조회합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "branch": {
                "type": "string",
                "description": "공유오피스 지점명",
                "enum": BRANCH_ENUM,
            },
            "room_name": {
                "type": "string",
                "description": "조회할 공간 이름",
            },
        },
        "required": [
            "branch",
            "room_name",
        ],
    },
}


question = "판교 지점의 프로젝트룸03 정보를 확인해줘."

interaction = client.interactions.create(
    model=MODEL_NAME,
    input=question,
    tools=[get_room_info_tool],
)

print("interaction status:", interaction.status)

function_calls = [
    step
    for step in interaction.steps or []
    if getattr(step, "type", None) == "function_call"
]

for index, call in enumerate(function_calls, start=1):
    call_id = (
        getattr(call, "call_id", None)
        or getattr(call, "id", None)
    )

    print(f"\n[Function call #{index}]")
    print("call id:", call_id)
    print("function name:", getattr(call, "name", None))
    print("arguments:", getattr(call, "arguments", None))
