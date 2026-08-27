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
        "특정 지점의 특정 공간 하나의 상세 정보를 조회합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "branch": {
                "type": "string",
                "enum": BRANCH_ENUM,
            },
            "room_name": {
                "type": "string",
                "enum": ROOM_ENUM,
            },
        },
        "required": ["branch", "room_name"],
    },
}

get_rooms_by_branch_tool = {
    "type": "function",
    "name": "get_rooms_by_branch",
    "description": (
        "특정 공유오피스 지점에 존재하는 "
        "전체 공간 목록을 조회합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "branch": {
                "type": "string",
                "enum": BRANCH_ENUM,
            },
        },
        "required": ["branch"],
    },
}

get_rooms_by_min_capacity_tool = {
    "type": "function",
    "name": "get_rooms_by_min_capacity",
    "description": (
        "전체 지점에서 사용자가 지정한 최소 수용 인원 이상인 "
        "공간을 검색합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "minimum_capacity": {
                "type": "integer",
                "description": "필요한 최소 수용 인원",
                "minimum": 1,
                "maximum": 100,
            },
        },
        "required": ["minimum_capacity"],
    },
}

search_video_rooms_tool = {
    "type": "function",
    "name": "search_video_rooms",
    "description": (
        "화상회의가 가능한 공간 중 최소 수용 인원 이상이고 "
        "사용자가 지정한 최대 시간당 가격 이하인 공간을 검색합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "minimum_capacity": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
            },
            "maximum_hourly_price": {
                "type": "integer",
                "minimum": 5000,
                "maximum": 200000,
            },
        },
        "required": [
            "minimum_capacity",
            "maximum_hourly_price",
        ],
    },
}

TOOLS = [
    get_room_info_tool,
    get_rooms_by_branch_tool,
    get_rooms_by_min_capacity_tool,
    search_video_rooms_tool,
]


def analyze_function_selection(
    question: str,
    expected_function: str | None,
) -> None:

    print_title(f"질문: {question}")

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=question,
        tools=TOOLS,
    )

    function_calls = [
        step
        for step in interaction.steps or []
        if getattr(step, "type", None) == "function_call"
    ]

    if not function_calls:
        print("실제 선택 Function: 없음")
        print("예상 Function:", expected_function)

        if interaction.output_text:
            print("Gemini 답변:", interaction.output_text)

        print(
            "일치 여부:",
            expected_function is None,
        )
        return

    selected_names = []

    for call in function_calls:
        function_name = getattr(call, "name", None)
        arguments = getattr(call, "arguments", None)

        selected_names.append(function_name)

        print("function:", function_name)
        print("arguments:", arguments)

    print("예상 Function:", expected_function)
    print("실제 선택 Function:", selected_names)
    print(
        "일치 여부:",
        expected_function in selected_names
        if expected_function is not None
        else False,
    )


TESTS = [
    ("여의도 미팅룸07 정보를 알려줘.", "get_room_info"),
    ("성수 지점에 있는 공간을 전부 보여줘.", "get_rooms_by_branch"),
    ("20명 이상 들어갈 수 있는 공간을 찾아줘.", "get_rooms_by_min_capacity"),
    (
        "화상회의가 가능하고 8명 이상 들어가며 "
        "시간당 35000원 이하인 공간을 찾아줘.",
        "search_video_rooms",
    ),
    ("Python의 dict와 list 차이를 설명해줘.", None),
]

for question, expected_function in TESTS:
    analyze_function_selection(
        question=question,
        expected_function=expected_function,
    )
