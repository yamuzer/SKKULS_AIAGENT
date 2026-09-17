import csv
import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from langchain.tools import tool, ToolRuntime
from langchain.messages import (
    HumanMessage,
    ToolMessage,
    AIMessage,
    SystemMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

EMPLOYEE_PATH = DATA_DIR / "employees_800.csv"
POLICY_PATH = DATA_DIR / "benefit_policies_1080.csv"


load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash",
)

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY가 없습니다.")


def load_csv(path: Path) -> list[dict]:

    with path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        return list(csv.DictReader(csv_file))


EMPLOYEES = load_csv(EMPLOYEE_PATH)
POLICIES = load_csv(POLICY_PATH)

EMPLOYEE_BY_ID = {
    row["user_id"]: row
    for row in EMPLOYEES
}


def get_region_group(region: str) -> str:

    if region in {"서울", "판교"}:
        return "수도권"

    if region == "제주":
        return "제주"

    return "비수도권"


class AgentState(MessagesState):

    user_id: str
    user_name: str
    department: str
    role: str
    region: str
    tool_rounds: int


@tool
def get_current_user_profile(
    runtime: ToolRuntime
) -> dict:
    """
    현재 대화 사용자의 프로필을 LangGraph State에서 조회한다.

    현재 사용자의 이름, 부서, 직급, 근무지역을 확인해야 할 때 사용한다.
    사용자 정보를 Tool Argument로 입력하지 않는다.
    """

    state = runtime.state

    return {
        "user_id": state.get("user_id"),
        "user_name": state.get("user_name"),
        "department": state.get("department"),
        "role": state.get("role"),
        "region": state.get("region"),
    }


@tool
def search_my_policy(
    topic: str,
    runtime: ToolRuntime,
) -> dict:
    """
    현재 사용자의 부서, 직급, 근무지역 기준으로
    사내 복지 또는 출장 정책을 조회한다.

    모델은 topic만 입력한다.
    department, role, region은 ToolRuntime을 통해 State에서 읽는다.
    """

    state = runtime.state

    department = state.get("department")
    role = state.get("role")
    region = state.get("region")

    region_group = get_region_group(region)

    for row in POLICIES:

        if (
            row["department"] == department
            and row["role"] == role
            and row["region_group"] == region_group
            and row["topic"] == topic
        ):

            return {
                "found": True,
                "topic": topic,
                "department": department,
                "role": role,
                "region": region,
                "region_group": region_group,
                "policy_id": row["policy_id"],
                "summary": row["summary"],
                "requires_approval": row["requires_approval"],
                "approval_level": row["approval_level"],
            }

    return {
        "found": False,
        "topic": topic,
        "department": department,
        "role": role,
        "region": region,
    }


@tool
def get_last_user_message(
    runtime: ToolRuntime
) -> dict:
    """
    현재 LangGraph State에서 가장 최근 HumanMessage를 확인한다.
    """

    messages = runtime.state.get(
        "messages",
        [],
    )

    for message in reversed(messages):

        if isinstance(message, HumanMessage):

            return {
                "found": True,
                "message": message.content,
            }

    return {
        "found": False,
        "message": None,
    }


@tool
def get_conversation_state_info(
    runtime: ToolRuntime
) -> dict:
    """
    현재 LangGraph State의 사용자 정보,
    메시지 수, Tool Round를 조회한다.
    """

    state = runtime.state
    messages = state.get("messages", [])

    return {
        "message_count": len(messages),
        "user_id": state.get("user_id"),
        "user_name": state.get("user_name"),
        "department": state.get("department"),
        "role": state.get("role"),
        "region": state.get("region"),
        "tool_rounds": state.get("tool_rounds", 0),
    }


tools = [
    get_current_user_profile,
    search_my_policy,
    get_last_user_message,
    get_conversation_state_info,
]


def print_tool_schemas():

    print("\n" + "=" * 80)
    print("Tool Schemas")
    print("=" * 80)

    for tool_object in tools:

        schema_object = tool_object.tool_call_schema

        if isinstance(schema_object, dict):
            schema = schema_object
        else:
            schema = schema_object.model_json_schema()

        print("\n" + "-" * 80)
        print(tool_object.name)

        print(
            json.dumps(
                schema,
                ensure_ascii=False,
                indent=2,
            )
        )

        properties = schema.get(
            "properties",
            {},
        )

        print(
            "LLM Arguments:",
            list(properties.keys()),
        )

        print(
            "runtime exposed:",
            "runtime" in properties,
        )


model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0,
    max_retries=2,
)

model_with_tools = model.bind_tools(tools)


SYSTEM_PROMPT = """
당신은 현재 LangGraph State에 저장된
사용자 정보를 활용하는 사내 정책 Agent입니다.

규칙:

1. 현재 사용자 이름, 부서, 직급, 근무지역을 추측하지 마세요.
2. 현재 사용자 프로필이 필요한 경우 get_current_user_profile을 사용하세요.
3. 사내 복지/출장 정책 질문은 search_my_policy를 사용하세요.
4. search_my_policy에는 topic만 전달하세요.
   department, role, region을 Argument로 만들지 마세요.
5. 사용자가 마지막으로 입력한 메시지를 물으면 get_last_user_message를 사용하세요.
6. 현재 State 정보가 필요하면 get_conversation_state_info를 사용하세요.
7. 일반 Python 개념처럼 State가 필요 없는 질문은 Tool 없이 직접 답할 수 있습니다.
8. 같은 정보를 얻기 위해 같은 Tool을 반복 호출하지 마세요.
"""


MAX_TOOL_ROUNDS = 5


def agent_node(
    state: AgentState
):

    messages = state["messages"]

    tool_rounds = state.get(
        "tool_rounds",
        0,
    )

    if tool_rounds >= MAX_TOOL_ROUNDS:

        return {
            "messages": [
                AIMessage(
                    content="Tool 호출 횟수 제한에 도달했습니다."
                )
            ]
        }

    response = model_with_tools.invoke(
        [
            SystemMessage(
                content=SYSTEM_PROMPT
            ),
            *messages,
        ]
    )

    if response.tool_calls:

        return {
            "messages": [
                response
            ],
            "tool_rounds": tool_rounds + 1,
        }

    return {
        "messages": [
            response
        ]
    }


tool_node = ToolNode(
    tools,
    handle_tool_errors=True,
)


def route_after_agent(
    state: AgentState
) -> Literal[
    "tools",
    "end",
]:

    last_message = state["messages"][-1]

    tool_calls = getattr(
        last_message,
        "tool_calls",
        [],
    )

    if tool_calls:
        return "tools"

    return "end"


builder = StateGraph(
    AgentState
)

builder.add_node(
    "agent",
    agent_node,
)

builder.add_node(
    "tools",
    tool_node,
)

builder.add_edge(
    START,
    "agent",
)

builder.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "tools": "tools",
        "end": END,
    },
)

builder.add_edge(
    "tools",
    "agent",
)

agent_graph = builder.compile()


def extract_tool_sequence(
    messages
) -> list[str]:

    sequence = []

    for message in messages:

        if not isinstance(
            message,
            AIMessage,
        ):
            continue

        for tool_call in message.tool_calls:

            sequence.append(
                tool_call.get("name")
            )

    return sequence


def load_user(
    user_id: str
) -> dict:

    row = EMPLOYEE_BY_ID.get(
        user_id
    )

    if row is None:

        raise ValueError(
            f"사용자 없음: {user_id}"
        )

    return row


def run_agent(
    question: str,
    user_id: str = "USR-0137",
):

    user = load_user(
        user_id
    )

    initial_state = {
        "messages": [
            HumanMessage(
                content=question
            )
        ],
        "user_id": user["user_id"],
        "user_name": user["user_name"],
        "department": user["department"],
        "role": user["role"],
        "region": user["region"],
        "tool_rounds": 0,
    }

    result = agent_graph.invoke(
        initial_state,
        config={
            "recursion_limit": 15
        },
    )

    print("\n" + "=" * 80)
    print("Execution History")
    print("=" * 80)

    for index, message in enumerate(
        result["messages"],
        start=1,
    ):

        print(
            f"\n[{index}] "
            f"{type(message).__name__}"
        )

        if isinstance(
            message,
            ToolMessage,
        ):
            print(
                "Tool:",
                message.name,
            )

        if (
            isinstance(
                message,
                AIMessage,
            )
            and message.tool_calls
        ):

            for call in message.tool_calls:
                print(
                    "Tool Call:",
                    call,
                )

        text = getattr(
            message,
            "text",
            None,
        )

        if (
            isinstance(
                text,
                str,
            )
            and text
        ):
            print(text)

        elif getattr(
            message,
            "content",
            None,
        ):
            print(message.content)

    sequence = extract_tool_sequence(
        result["messages"]
    )

    print("\nTool Sequence:")

    if sequence:
        print(
            " -> ".join(sequence)
        )
    else:
        print(
            "Tool 사용 안 함"
        )

    print(
        "\n총 Tool Round:",
        result.get(
            "tool_rounds",
            0,
        ),
    )

    final_message = result["messages"][-1]

    final_text = getattr(
        final_message,
        "text",
        None,
    )

    print("\nFinal Answer:")

    if (
        isinstance(
            final_text,
            str,
        )
        and final_text
    ):
        print(final_text)
    else:
        print(
            final_message.content
        )

    return result


if __name__ == "__main__":

    print_tool_schemas()

    run_agent(
        "내 부서와 직급 기준 출장숙박비 정책을 알려줘."
    )
