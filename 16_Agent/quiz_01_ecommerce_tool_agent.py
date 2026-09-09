import csv
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.tools import tool
from langchain.messages import (
    HumanMessage,
    ToolMessage,
    AIMessage,
    SystemMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import (
    START,
    END,
    MessagesState,
    StateGraph,
)
from langgraph.prebuilt import ToolNode


BASE_DIR = Path(__file__).resolve().parent.parent


DATA_DIR =  BASE_DIR / "data"

PRODUCT_PATH = DATA_DIR / "products_600.csv"

WAREHOUSE_PATH = DATA_DIR / "warehouses_12.csv"

INVENTORY_PATH = DATA_DIR / "inventory_7200.csv"

SHIPPING_PATH = DATA_DIR / "shipping_rules_1344.csv"


load_dotenv(BASE_DIR / ".env")


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash",
)


if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY가 없습니다."
    )


def load_csv(
    path: Path
) -> list[dict]:

    with path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        return list(csv.DictReader(csv_file))


PRODUCTS = load_csv(PRODUCT_PATH)

WAREHOUSES = load_csv(WAREHOUSE_PATH)

INVENTORY = load_csv(INVENTORY_PATH)

SHIPPING_RULES = load_csv(SHIPPING_PATH)


PRODUCT_BY_ID = {
    row["product_id"]: row
    for row in PRODUCTS
}

WAREHOUSE_BY_ID = {
    row["warehouse_id"]: row
    for row in WAREHOUSES
}


class InventoryInput(BaseModel):

    product_id: str = Field(
        min_length=5,
        description=(
            "재고를 조회할 상품 ID. "
            "예: PRD-0247"
        ),
    )

    required_quantity: int = Field(
        ge=1,
        le=100,
        description="주문에 필요한 최소 상품 수량",
    )


class CheckoutInput(BaseModel):

    unit_price: int = Field(
        ge=0
    )

    quantity: int = Field(
        ge=1,
        le=100
    )

    shipping_fee: int = Field(
        ge=0
    )


@tool
def find_product(
    product_id: str
) -> dict:
    """
    상품 ID로 상품 정보를 조회한다.

    상품명, 단가, 무게, 판매 가능 여부를 확인해야 할 때 사용한다.
    재고와 배송 정보는 반환하지 않는다.
    """

    print("\n" + "=" * 70)
    print("[Tool: find_product]")
    print("=" * 70)

    row = PRODUCT_BY_ID.get(
        product_id
    )

    if row is None:
        return {
            "found": False,
            "product_id": product_id,
        }

    return {
        "found": True,
        "product_id":
            row["product_id"],
        "product_name":
            row["product_name"],
        "category_name":
            row["category_name"],
        "unit_price":
            int(
                row["unit_price"]
            ),
        "weight_kg":
            float(
                row["weight_kg"]
            ),
        "active":
            row["active"],
        "fragile":
            row["fragile"],
    }


@tool(args_schema=InventoryInput)
def find_available_inventory(
    product_id: str,
    required_quantity: int,
) -> dict:
    """
    특정 상품을 필요한 수량 이상 보유한 창고를 찾는다.

    상품 ID와 구매 수량을 모두 알고 있을 때 사용한다.
    가능한 창고는 priority_rank가 낮은 순서로 반환한다.
    """

    print("\n" + "=" * 70)
    print("[Tool: find_available_inventory]")
    print("=" * 70)

    matches = []

    for row in INVENTORY:

        if (row["product_id"] != product_id):
            continue

        available_qty = int(
            row["available_qty"]
        )

        if (available_qty < required_quantity):
            continue

        warehouse = (
            WAREHOUSE_BY_ID.get(
                row["warehouse_id"]
            )
        )

        if warehouse is None:
            continue

        matches.append(
            {
                "warehouse_id":
                    row["warehouse_id"],
                "warehouse_name":
                    warehouse[
                        "warehouse_name"
                    ],
                "region":
                    warehouse["region"],
                "available_qty":
                    available_qty,
                "priority_rank":
                    int(
                        warehouse[
                            "priority_rank"
                        ]
                    ),
            }
        )

    matches.sort(
        key=lambda item: (
            item["priority_rank"],
            -item["available_qty"],
        )
    )

    return {
        "found":
            len(matches) > 0,
        "product_id":
            product_id,
        "required_quantity":
            required_quantity,
        "warehouses":
            matches,
    }


@tool
def find_shipping_rule(
    warehouse_id: str,
    destination_region: str,
    total_weight_kg: float,
) -> dict:
    """
    출고 창고, 배송 지역, 주문 전체 무게에 맞는
    배송비와 예상 배송일을 조회한다.

    warehouse_id와 total_weight_kg를 모르면
    다른 Tool로 먼저 확인해야 한다.
    """

    print("\n" + "=" * 70)
    print("[Tool: find_shipping_rule]")
    print("=" * 70)

    for row in SHIPPING_RULES:
        if (row["warehouse_id"] != warehouse_id):
            continue

        if (row["destination_region"] != destination_region):
            continue

        min_weight = float(
            row["min_weight_kg"]
        )

        max_weight = float(
            row["max_weight_kg"]
        )

        if (
            total_weight_kg > min_weight
            and total_weight_kg <= max_weight
        ):
            return {
                "found": True,
                "warehouse_id":
                    warehouse_id,
                "destination_region":
                    destination_region,
                "total_weight_kg":
                    total_weight_kg,
                "shipping_fee":
                    int(
                        row["shipping_fee"]
                    ),
                "estimated_days":
                    int(
                        row[
                            "estimated_days"
                        ]
                    ),
            }

    return {
        "found": False,
        "warehouse_id":
            warehouse_id,
        "destination_region":
            destination_region,
        "total_weight_kg":
            total_weight_kg,
    }


@tool(args_schema=CheckoutInput)
def calculate_checkout_total(
    unit_price: int,
    quantity: int,
    shipping_fee: int,
) -> dict:
    """
    상품 단가, 주문 수량, 배송비로
    상품 총액과 최종 예상 결제액을 계산한다.
    """

    print("\n" + "=" * 70)
    print("[Tool: calculate_checkout_total]")
    print("=" * 70)

    product_total = unit_price * quantity

    checkout_total = product_total + shipping_fee

    return {
        "unit_price":
            unit_price,
        "quantity":
            quantity,
        "product_total":
            product_total,
        "shipping_fee":
            shipping_fee,
        "checkout_total":
            checkout_total,
    }


tools = [
    find_product,
    find_available_inventory,
    find_shipping_rule,
    calculate_checkout_total,
]


model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0,
    max_retries=2,
)


model_with_tools = model.bind_tools(tools)


SYSTEM_PROMPT = """
당신은 온라인 쇼핑몰 주문·재고·배송을 처리하는 Tool-Using Agent입니다.

반드시 다음 규칙을 지키세요.

1. 상품 ID의 상품명, 단가, 무게를 확인해야 하면 find_product를 사용하세요.

2. 특정 수량을 주문할 수 있는 창고가 필요한 경우
   find_available_inventory를 사용하세요.

3. 배송비를 계산하려면 warehouse_id와 전체 주문 무게가 필요합니다.
   값을 모르면 추측하지 말고 다른 Tool을 먼저 사용하세요.

4. 전체 주문 무게는
   상품 1개 무게 × 주문 수량으로 계산할 수 있습니다.

5. 배송비와 상품 금액을 모두 확인한 뒤
   calculate_checkout_total을 사용하세요.

6. 가능한 창고가 여러 개이면
   priority_rank가 가장 낮은 창고를 우선 선택하세요.

7. 상품이 판매 중지(active=N)이면
   주문 가능하다고 답하지 마세요.

8. Tool 결과에 없는 상품, 재고, 배송 정보를 만들지 마세요.

9. Tool이 found=False를 반환했다면 같은 Tool을 같은 입력값으로 반복 호출하지 마세요.
   다른 유효한 입력을 얻을 수 없다면 해당 조건에서는 처리할 수 없다고 답하세요.

10. 필요한 정보가 모두 모이면 Tool 호출을 종료하고
    자연스러운 한국어로 최종 답변하세요.

11. 단순한 일반상식 질문에는
    쇼핑몰 Tool을 억지로 사용하지 마세요.
"""


MAX_TOOL_ROUNDS = 6


class AgentState(MessagesState):

    tool_rounds: int


def agent_node(state: AgentState):

    print("\n" + "=" * 70)
    print("[Agent Node]")
    print("=" * 70)

    messages = state["messages"]

    tool_rounds = state.get(
                    "tool_rounds",
                    0,
    )

    if tool_rounds >= MAX_TOOL_ROUNDS:

        return {
            "messages": [
                AIMessage(
                    content=(
                        "도구 호출 횟수 제한에 도달하여 "
                        "요청을 완료하지 못했습니다."
                    )
                )
            ]
        }

    model_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *messages,
    ]

    response = model_with_tools.invoke(model_messages)

    print("\n[Tool Calls]")
    print(response.tool_calls)

    if response.tool_calls:

        return {
            "messages": [
                response
            ],
            "tool_rounds":
                tool_rounds + 1,
        }

    return {
        "messages": [
            response
        ]
    }


tool_node = ToolNode(tools)


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


builder = StateGraph(AgentState)

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


def print_message(
    index: int,
    message,
):

    print("\n" + "-" * 70)

    print(
        f"Message {index} "
        f"({type(message).__name__})"
    )

    if isinstance(message, ToolMessage):

        print(f"Tool: {message.name}")

    if isinstance( message,AIMessage,) and message.tool_calls:

        print("Tool Calls:")

        for call in message.tool_calls:

            print(
                call
            )

    text = getattr(
        message,
        "text",
        None,
    )

    if isinstance(text, str) and text:
        print(text)

    elif getattr(message, "content", None):
        print(message.content)


def run_agent(
    question: str
):

    print("\n" + "#" * 80)

    print(question)

    print("#" * 80)

    initial_state = {
        "messages": [
            HumanMessage(
                content=question
            )
        ],
        "tool_rounds": 0,
    }

    result = (
        agent_graph.invoke(
            initial_state,
            config={
                "recursion_limit": 20
            },
        )
    )

    print(
        "\n총 Tool Round:",
        result.get(
            "tool_rounds",
            0,
        ),
    )

    for index, message in enumerate(result["messages"], start=1):

        print_message(
            index,
            message,
        )

    print("\n" + "=" * 80)
    print("Final Answer")
    print("=" * 80)

    final_message = result["messages"][-1]

    final_text = getattr(
        final_message,
        "text",
        None,
    )

    if isinstance(final_text, str) and final_text:
        print(final_text)

    else:
        print(final_message.content)

    return result


if __name__ == "__main__":

    run_agent(
        "PRD-0247 상품 4개를 부산으로 보내려고 합니다. "
        "주문 가능한 창고를 찾아서 상품 금액, 배송비, "
        "최종 예상 결제액과 예상 배송일을 알려주세요."
    )
