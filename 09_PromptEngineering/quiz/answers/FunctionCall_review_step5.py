import csv
import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, ConfigDict, Field, ValidationError


# ============================================================
# 1. 기본 설정
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
CSV_PATH = BASE_DIR / "data" / "cowork_room_info.csv"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY를 읽을 수 없습니다."
    )

if not CSV_PATH.exists():
    raise FileNotFoundError(
        f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}"
    )

client = genai.Client(
    api_key=api_key
)

MODEL_NAME = "gemini-3.7-flash"


# ============================================================
# 2. CSV 읽기
# ============================================================

def load_room_data(
    csv_path: Path,
) -> list[dict]:

    data = []

    with csv_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:

            row["floor"] = int(
                row["floor"]
            )

            row["capacity"] = int(
                row["capacity"]
            )

            row["monitor_count"] = int(
                row["monitor_count"]
            )

            row["pc_count"] = int(
                row["pc_count"]
            )

            row["hourly_price"] = int(
                row["hourly_price"]
            )

            data.append(row)

    return data


ROOM_DATA = load_room_data(
    CSV_PATH
)


# ============================================================
# 3. Helper
# ============================================================

def normalize_text(
    value: str,
) -> str:

    return value.strip()


def yn_to_bool(
    value: str,
) -> bool:

    return (
        value.strip().upper()
        == "Y"
    )


def convert_room(
    room: dict,
) -> dict:

    return {
        "branch": room["branch"],
        "building": room["building"],
        "room_name": room["room_name"],
        "floor": room["floor"],
        "room_type": room["room_type"],
        "capacity": room["capacity"],
        "monitor_count": room["monitor_count"],
        "pc_count": room["pc_count"],
        "video_conference": yn_to_bool(
            room["video_conference"]
        ),
        "whiteboard": yn_to_bool(
            room["whiteboard"]
        ),
        "wifi": yn_to_bool(
            room["wifi"]
        ),
        "accessibility": yn_to_bool(
            room["accessibility"]
        ),
        "hourly_price": room["hourly_price"],
        "status": room["status"],
    }


# ============================================================
# 4. 실제 Python Function
# ============================================================

def get_room_info(
    branch: str,
    room_name: str,
) -> dict:

    branch = normalize_text(branch)
    room_name = normalize_text(room_name)

    for room in ROOM_DATA:

        if (
            room["branch"] == branch
            and
            room["room_name"] == room_name
        ):
            return {
                "success": True,
                "data": convert_room(room),
            }

    return {
        "success": False,
        "message": "조건에 맞는 공간을 찾을 수 없습니다.",
        "query": {
            "branch": branch,
            "room_name": room_name,
        },
    }


def get_rooms_by_branch(
    branch: str,
) -> dict:

    branch = normalize_text(branch)

    matched = [
        convert_room(room)
        for room in ROOM_DATA
        if room["branch"] == branch
    ]

    return {
        "success": bool(matched),
        "branch": branch,
        "count": len(matched),
        "data": matched,
    }


def get_rooms_by_min_capacity(
    minimum_capacity: int,
) -> dict:

    matched = [
        convert_room(room)
        for room in ROOM_DATA
        if room["capacity"] >= minimum_capacity
    ]

    matched.sort(
        key=lambda item: (
            -item["capacity"],
            item["hourly_price"],
        )
    )

    return {
        "success": True,
        "minimum_capacity": minimum_capacity,
        "count": len(matched),
        "data": matched,
    }


def search_video_rooms(
    minimum_capacity: int,
    maximum_hourly_price: int,
) -> dict:

    matched = [
        convert_room(room)
        for room in ROOM_DATA
        if (
            yn_to_bool(
                room["video_conference"]
            )
            and
            room["capacity"] >= minimum_capacity
            and
            room["hourly_price"] <= maximum_hourly_price
            and
            room["status"] == "AVAILABLE"
        )
    ]

    matched.sort(
        key=lambda item: (
            item["hourly_price"],
            -item["capacity"],
        )
    )

    return {
        "success": True,
        "minimum_capacity": minimum_capacity,
        "maximum_hourly_price": maximum_hourly_price,
        "count": len(matched),
        "data": matched,
    }


# ============================================================
# 5. FUNCTION_MAP
# ============================================================

FUNCTION_MAP = {
    "get_room_info":
        get_room_info,

    "get_rooms_by_branch":
        get_rooms_by_branch,

    "get_rooms_by_min_capacity":
        get_rooms_by_min_capacity,

    "search_video_rooms":
        search_video_rooms,
}


# ============================================================
# 6. Function Declaration
# ============================================================

BRANCH_VALUES = [
    "강남", "여의도", "판교", "광화문", "성수", "잠실",
    "마곡", "구로", "수원", "인천", "대전", "부산",
]

ROOM_VALUES = [
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
        "수용 인원, PC 수, 화상회의 가능 여부, "
        "시간당 가격, 현재 상태 등의 상세 정보를 조회합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "branch": {
                "type": "string",
                "description": "공유오피스 지점",
                "enum": BRANCH_VALUES,
            },
            "room_name": {
                "type": "string",
                "description": "공간 이름",
                "enum": ROOM_VALUES,
            },
        },
        "required": [
            "branch",
            "room_name",
        ],
    },
}


get_rooms_by_branch_tool = {
    "type": "function",
    "name": "get_rooms_by_branch",
    "description": (
        "특정 공유오피스 지점에 있는 "
        "전체 공간 목록을 조회합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "branch": {
                "type": "string",
                "description": "공유오피스 지점",
                "enum": BRANCH_VALUES,
            },
        },
        "required": [
            "branch",
        ],
    },
}


get_rooms_by_min_capacity_tool = {
    "type": "function",
    "name": "get_rooms_by_min_capacity",
    "description": (
        "전체 공유오피스 공간 중 사용자가 지정한 "
        "최소 수용 인원 이상인 공간을 검색합니다."
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
        "required": [
            "minimum_capacity",
        ],
    },
}


search_video_rooms_tool = {
    "type": "function",
    "name": "search_video_rooms",
    "description": (
        "화상회의가 가능한 공유오피스 공간 중 "
        "최소 수용 인원 이상이며 최대 시간당 가격 이하이고 "
        "현재 이용 가능한 공간을 검색합니다."
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
            "maximum_hourly_price": {
                "type": "integer",
                "description": "허용 가능한 최대 시간당 가격",
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


# ============================================================
# 7. Pydantic Argument Model
# ============================================================

BranchType = Literal[
    "강남", "여의도", "판교", "광화문", "성수", "잠실",
    "마곡", "구로", "수원", "인천", "대전", "부산",
]

RoomNameType = Literal[
    "미팅룸01", "미팅룸02", "미팅룸03", "미팅룸04", "미팅룸05",
    "미팅룸06", "미팅룸07", "미팅룸08", "미팅룸09", "미팅룸10",
    "프로젝트룸01", "프로젝트룸02", "프로젝트룸03", "프로젝트룸04", "프로젝트룸05",
    "화상회의실01", "화상회의실02", "화상회의실03", "화상회의실04", "화상회의실05",
    "세미나실01", "세미나실02", "세미나실03",
    "포커스룸01", "포커스룸02",
]


class RoomInfoArguments(
    BaseModel
):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    branch: BranchType
    room_name: RoomNameType


class RoomsByBranchArguments(
    BaseModel
):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    branch: BranchType


class RoomsByMinCapacityArguments(
    BaseModel
):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    minimum_capacity: int = Field(
        ge=1,
        le=100,
    )


class SearchVideoRoomsArguments(
    BaseModel
):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    minimum_capacity: int = Field(
        ge=1,
        le=100,
    )

    maximum_hourly_price: int = Field(
        ge=5000,
        le=200000,
    )


ARGUMENT_MODEL_MAP = {
    "get_room_info":
        RoomInfoArguments,

    "get_rooms_by_branch":
        RoomsByBranchArguments,

    "get_rooms_by_min_capacity":
        RoomsByMinCapacityArguments,

    "search_video_rooms":
        SearchVideoRoomsArguments,
}


# ============================================================
# 8. Argument Validation
# ============================================================

def validate_function_arguments(
    function_name: str,
    arguments,
) -> dict:

    model_class = (
        ARGUMENT_MODEL_MAP.get(
            function_name
        )
    )

    if model_class is None:
        return {
            "valid": False,
            "data": None,
            "errors": [
                {
                    "message": (
                        "등록되지 않은 Function입니다."
                    )
                }
            ],
        }

    if not isinstance(
        arguments,
        dict,
    ):
        return {
            "valid": False,
            "data": None,
            "errors": [
                {
                    "message": (
                        "arguments는 dict여야 합니다."
                    )
                }
            ],
        }

    try:
        validated = (
            model_class
            .model_validate(
                arguments
            )
        )

        return {
            "valid": True,
            "data": (
                validated
                .model_dump()
            ),
            "errors": [],
        }

    except ValidationError as error:
        return {
            "valid": False,
            "data": None,
            "errors": (
                error.errors()
            ),
        }


# ============================================================
# 9. 실제 Python Function 실행
# ============================================================

def execute_function(
    function_name: str,
    validated_arguments: dict,
) -> dict:

    python_function = (
        FUNCTION_MAP.get(
            function_name
        )
    )

    if python_function is None:
        return {
            "success": False,
            "error": (
                "실행할 Python Function을 "
                "찾을 수 없습니다."
            ),
        }

    try:
        return python_function(
            **validated_arguments
        )

    except Exception as error:
        return {
            "success": False,
            "error_type": type(error).__name__,
            "error": str(error),
        }


# ============================================================
# 10. Function Result Input 생성
# ============================================================

def build_function_result_input(
    call,
    function_result: dict,
) -> dict:

    return {
        "type": "function_result",
        "name": call.name,
        "call_id": call.id,
        "result": [
            {
                "type": "text",
                "text": json.dumps(
                    function_result,
                    ensure_ascii=False,
                ),
            }
        ],
    }


# ============================================================
# 11. 한 질문을 끝까지 처리
# ============================================================

def process_question(
    question: str,
) -> None:

    print(
        "\n"
        + "=" * 90
    )
    print("사용자 질문")
    print("=" * 90)
    print(question)

    # --------------------------------------------------------
    # TURN 1
    # 사용자 질문 + Function Declaration
    # --------------------------------------------------------

    first_interaction = (
        client.interactions.create(
            model=MODEL_NAME,
            input=question,
            tools=TOOLS,
            generation_config={
                "tool_choice": "any",
            },
        )
    )

    print("\n[TURN 1]")
    print(
        "interaction.id:",
        first_interaction.id,
    )
    print(
        "status:",
        first_interaction.status,
    )

    function_calls = [
        step
        for step in (
            first_interaction.steps
            or []
        )
        if getattr(
            step,
            "type",
            None,
        ) == "function_call"
    ]

    if not function_calls:
        print(
            "Function Call이 없습니다."
        )
        if first_interaction.output_text:
            print(
                first_interaction.output_text
            )
        return

    function_result_inputs = []

    for index, call in enumerate(
        function_calls,
        start=1,
    ):

        print(
            "\n"
            + "-" * 70
        )
        print(
            f"Function Call #{index}"
        )
        print("-" * 70)

        print("call.id:", call.id)
        print("call.name:", call.name)
        print(
            "call.arguments:",
            call.arguments,
        )

        # ----------------------------------------------------
        # A. Arguments Validation
        # ----------------------------------------------------

        validation = (
            validate_function_arguments(
                function_name=call.name,
                arguments=call.arguments,
            )
        )

        print(
            "\nValidation:",
            validation["valid"],
        )

        if not validation["valid"]:

            print(
                "Function 실행을 차단합니다."
            )

            for error in validation["errors"]:
                print("-", error)

            continue

        validated_arguments = (
            validation["data"]
        )

        # ----------------------------------------------------
        # B. 실제 Python Function 실행
        # ----------------------------------------------------

        function_result = (
            execute_function(
                function_name=call.name,
                validated_arguments=(
                    validated_arguments
                ),
            )
        )

        print(
            "\n[실제 Python Function Result]"
        )
        print(
            json.dumps(
                function_result,
                ensure_ascii=False,
                indent=2,
            )
        )

        # ----------------------------------------------------
        # C. Gemini에게 전달할 function_result 생성
        # ----------------------------------------------------

        function_result_input = (
            build_function_result_input(
                call=call,
                function_result=(
                    function_result
                ),
            )
        )

        function_result_inputs.append(
            function_result_input
        )

    if not function_result_inputs:
        print(
            "\n정상적인 Function Result가 없어 "
            "TURN 2를 진행하지 않습니다."
        )
        return

    # --------------------------------------------------------
    # TURN 2
    # Function Result + previous_interaction_id
    # --------------------------------------------------------

    final_interaction = (
        client.interactions.create(
            model=MODEL_NAME,
            previous_interaction_id=(
                first_interaction.id
            ),
            tools=TOOLS,
            input=(
                function_result_inputs
            ),
        )
    )

    print(
        "\n"
        + "=" * 90
    )
    print(
        "[TURN 2 - Function Result 반환]"
    )
    print("=" * 90)

    print(
        "previous_interaction_id:",
        first_interaction.id,
    )

    print(
        "final interaction.id:",
        final_interaction.id,
    )

    print(
        "status:",
        final_interaction.status,
    )

    print(
        "\nGemini 최종 답변"
    )
    print("-" * 90)
    print(
        final_interaction.output_text
    )


# ============================================================
# 12. Test
# ============================================================

TEST_QUESTIONS = [
    (
        "판교 프로젝트룸03의 수용 인원, PC 수, "
        "화상회의 가능 여부와 시간당 가격을 알려줘."
    ),
    (
        "부산 지점에 공간이 몇 개 있는지 확인하고 "
        "공간 이름을 간단히 알려줘."
    ),
    (
        "30명 이상 들어갈 수 있는 공간을 찾아서 "
        "수용 인원이 큰 순서대로 5개만 알려줘."
    ),
    (
        "화상회의가 가능하고 10명 이상 들어가며 "
        "시간당 40000원 이하이고 현재 이용 가능한 공간을 "
        "가격이 저렴한 순으로 5개 알려줘."
    ),
]


for question in TEST_QUESTIONS:
    process_question(
        question
    )
