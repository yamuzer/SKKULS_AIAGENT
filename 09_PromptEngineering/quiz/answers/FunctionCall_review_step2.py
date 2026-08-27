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

ROOM_ENUM = [
    "미팅룸01", "미팅룸02", "미팅룸03", "미팅룸04", "미팅룸05",
    "미팅룸06", "미팅룸07", "미팅룸08", "미팅룸09", "미팅룸10",
    "프로젝트룸01", "프로젝트룸02", "프로젝트룸03", "프로젝트룸04", "프로젝트룸05",
    "화상회의실01", "화상회의실02", "화상회의실03", "화상회의실04", "화상회의실05",
    "세미나실01", "세미나실02", "세미나실03",
    "포커스룸01", "포커스룸02",
]

get_room_info_tool = {
    "type": "function",
    "name": "get_room_info",
    "description": (
        "특정 공유오피스 지점의 특정 공간 하나에 대한 "
        "상세 정보를 조회합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "branch": {
                "type": "string",
                "description": "공유오피스 지점",
                "enum": BRANCH_ENUM,
            },
            "room_name": {
                "type": "string",
                "description": "공간 이름",
                "enum": ROOM_ENUM,
            },
        },
        "required": [
            "branch",
            "room_name",
        ],
    },
}


def test_function_call(question: str) -> None:
    print_title(f"질문: {question}")

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=question,
        tools=[get_room_info_tool],
    )

    print("interaction status:", interaction.status)

    steps = interaction.steps or []

    for index, step in enumerate(steps, start=1):
        print(
            f"[step {index}]",
            getattr(step, "type", None),
        )

    function_calls = [
        step
        for step in steps
        if getattr(step, "type", None) == "function_call"
    ]

    if not function_calls:
        print("Function Call이 없습니다.")
        if interaction.output_text:
            print("Gemini 답변:", interaction.output_text)
        return

    for index, call in enumerate(function_calls, start=1):
        call_id = (
            getattr(call, "call_id", None)
            or getattr(call, "id", None)
        )

        print(f"\n[Function call #{index}]")
        print("call id:", call_id)
        print("function name:", getattr(call, "name", None))
        print("arguments:", getattr(call, "arguments", None))


test_function_call("강남 미팅룸04의 정보를 확인해줘.")
test_function_call(
    "부산 화상회의실02의 수용 인원과 "
    "화상회의 가능 여부를 확인해줘."
)
test_function_call("대전 세미나실03의 정보를 알려줘.")
