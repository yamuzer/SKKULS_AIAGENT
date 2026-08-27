from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


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


class RoomInfoArguments(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    branch: BranchType
    room_name: RoomNameType


class RoomsByBranchArguments(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    branch: BranchType


class RoomsByMinCapacityArguments(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )

    minimum_capacity: int = Field(
        ge=1,
        le=100,
    )


class SearchVideoRoomsArguments(BaseModel):
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


def validate_function_arguments(
    function_name: str,
    arguments,
) -> dict:

    model_class = ARGUMENT_MODEL_MAP.get(
        function_name
    )

    if model_class is None:
        return {
            "valid": False,
            "data": None,
            "errors": [
                {
                    "type": "unknown_function",
                    "message": "등록되지 않은 Function입니다.",
                }
            ],
        }

    if not isinstance(arguments, dict):
        return {
            "valid": False,
            "data": None,
            "errors": [
                {
                    "type": "invalid_arguments_type",
                    "message": "arguments는 dict여야 합니다.",
                }
            ],
        }

    try:
        validated = model_class.model_validate(
            arguments
        )

        return {
            "valid": True,
            "data": validated.model_dump(),
            "errors": [],
        }

    except ValidationError as error:
        return {
            "valid": False,
            "data": None,
            "errors": error.errors(),
        }


BAD_ARGUMENT_TESTS = [
    (
        "필수 argument 누락",
        "get_room_info",
        {"branch": "강남"},
    ),
    (
        "enum에 없는 지점",
        "get_room_info",
        {"branch": "춘천", "room_name": "미팅룸01"},
    ),
    (
        "잘못된 자료형",
        "get_rooms_by_min_capacity",
        {"minimum_capacity": "20"},
    ),
    (
        "범위 미만",
        "get_rooms_by_min_capacity",
        {"minimum_capacity": 0},
    ),
    (
        "가격 범위 미만",
        "search_video_rooms",
        {
            "minimum_capacity": 8,
            "maximum_hourly_price": 3000,
        },
    ),
    (
        "불필요한 argument",
        "get_room_info",
        {
            "branch": "강남",
            "room_name": "미팅룸01",
            "capacity": 100,
        },
    ),
    (
        "등록되지 않은 Function",
        "delete_room",
        {"branch": "강남"},
    ),
]


for test_name, function_name, arguments in BAD_ARGUMENT_TESTS:
    print("\n" + "=" * 80)
    print("테스트:", test_name)
    print("Function:", function_name)
    print("Arguments:", arguments)

    result = validate_function_arguments(
        function_name=function_name,
        arguments=arguments,
    )

    print("valid:", result["valid"])

    if result["valid"]:
        print("data:", result["data"])
    else:
        print("errors:")
        for error in result["errors"]:
            print("-", error)
