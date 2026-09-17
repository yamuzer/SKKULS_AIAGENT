import csv
import json
import os
from collections import Counter
from pathlib import Path
from typing import TypedDict, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import START, END, StateGraph
from langgraph.types import Command


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

VOC_PATH = DATA_DIR / "customer_voc_1500.csv"
POLICY_PATH = DATA_DIR / "service_policies_240.csv"

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash",
)

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY가 없습니다."
    )


model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0,
    max_retries=2,
)


def get_response_text(response):

    text = getattr(response, "text", None)

    if isinstance(text, str) and text:
        return text

    content = getattr(response,"content", "")

    if isinstance(content, str):
        return content

    return str(content)


def load_csv(path):

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        return list(csv.DictReader(file))


VOC_ROWS = load_csv(VOC_PATH)
POLICY_ROWS = load_csv(POLICY_PATH)


PRODUCTS = [
    "SmartHome Hub",
    "AirPure Pro",
    "CleanBot X",
    "VisionCam",
    "FitBand",
    "SoundDock",
]

CATEGORIES = [
    "연결 오류",
    "앱 오류",
    "배송 지연",
    "초기 불량",
    "소음",
    "배터리",
    "계정 문제",
    "설치 문의",
]


class VOCMultiAgentState(TypedDict):

    question: str
    audience: str

    selected_agent: str
    route_reason: str
    route_confidence: int
    routed_task: str

    needs_writing: bool

    product_filter: str
    category_filter: str

    evidence_summary: str
    sample_vocs: list[str]
    policy_evidence: list[str]

    research_summary: str
    key_findings: list[str]
    risk_points: list[str]
    recommended_actions: list[str]
    recommended_structure: list[str]

    active_agent: str
    execution_order: list[str]

    final_answer: str


class RouterDecision(BaseModel):

    selected_agent: Literal[
        "research_agent",
        "explainer_agent",
    ] = Field(
        description="처음 실행할 Agent"
    )

    reason: str = Field(
        description="선택 이유"
    )

    confidence: int = Field(
        ge=0,
        le=100,
        description="Routing 판단 확신 지표",
    )

    task_for_agent: str = Field(
        description="선택 Agent가 수행할 구체적 작업"
    )

    needs_writing: bool = Field(
        description=(
            "Research 이후 Writer가 필요한지 여부"
        )
    )


class ResearchResult(BaseModel):

    summary: str
    key_findings: list[str]
    risk_points: list[str]
    recommended_actions: list[str]
    recommended_structure: list[str]


router_model = model.with_structured_output(
    RouterDecision
)

research_model = model.with_structured_output(
    ResearchResult
)


ROUTER_SYSTEM_PROMPT = '''
당신은 고객 VOC Multi-Agent 시스템의 Router입니다.

직접 VOC를 분석하거나 최종 보고서를 쓰지 마세요.

실제 VOC 데이터 분석이 필요하면
research_agent를 선택합니다.

개념 자체 설명이면
explainer_agent를 선택합니다.

"분석만", "보고서는 아직 만들지 마"
→ needs_writing=False

"보고서 작성", "발표용", "회의에서 바로 사용"
→ needs_writing=True

confidence는 정답 확률이 아니라
Router의 판단 확신 지표입니다.
'''


def router_node(
    state: VOCMultiAgentState
) -> Command[
    Literal[
        "research_agent",
        "explainer_agent",
    ]
]:

    decision = router_model.invoke(
        [
            SystemMessage(
                content=ROUTER_SYSTEM_PROMPT
            ),
            HumanMessage(
                content=f'''
사용자 질문:

{state["question"]}

대상 수준:

{state["audience"]}

가장 적합한 첫 Agent와
Writer 필요 여부를 판단하세요.
'''
            ),
        ]
    )

    return Command(
        update={
            "selected_agent":
                decision.selected_agent,
            "route_reason":
                decision.reason,
            "route_confidence":
                decision.confidence,
            "routed_task":
                decision.task_for_agent,
            "needs_writing":
                decision.needs_writing,
            "active_agent":
                decision.selected_agent,
            "execution_order": [
                *state.get(
                    "execution_order",
                    [],
                ),
                "router",
            ],
        },
        goto=decision.selected_agent,
    )


def detect_filter(question):

    product_filter = ""

    for product in PRODUCTS:

        if product.lower() in question.lower():
            product_filter = product
            break

    category_filter = ""

    for category in CATEGORIES:

        if category in question:
            category_filter = category
            break

    return (
        product_filter,
        category_filter,
    )


def build_evidence(question):

    (
        product_filter,
        category_filter,
    ) = detect_filter(question)

    filtered = []

    for row in VOC_ROWS:

        if (
            product_filter
            and
            row["product_line"] != product_filter
        ):
            continue

        if (
            category_filter
            and
            row["issue_category"] != category_filter
        ):
            continue

        filtered.append(row)

    if not filtered:
        filtered = VOC_ROWS

    total_count = len(filtered)

    avg_satisfaction = (
        sum(
            int(row["satisfaction_score"])
            for row in filtered
        )
        / total_count
    )

    avg_resolution = (
        sum(
            int(row["resolution_hours"])
            for row in filtered
        )
        / total_count
    )

    repeat_count = sum(
        1
        for row in filtered
        if row["repeat_contact"] == "Y"
    )

    repeat_rate = (
        repeat_count / total_count
        * 100
    )

    severity_counter = Counter(
        row["severity"]
        for row in filtered
    )

    channel_counter = Counter(
        row["channel"]
        for row in filtered
    )

    category_counter = Counter(
        row["issue_category"]
        for row in filtered
    )

    evidence_summary = (
        f"필터 Product: "
        f"{product_filter or '전체'}\n"
        f"필터 Category: "
        f"{category_filter or '전체'}\n"
        f"VOC 건수: "
        f"{total_count}\n"
        f"평균 만족도: "
        f"{avg_satisfaction:.2f}/5\n"
        f"평균 해결시간: "
        f"{avg_resolution:.2f}시간\n"
        f"반복 문의율: "
        f"{repeat_rate:.2f}%\n"
        f"Severity 분포: "
        f"{dict(severity_counter)}\n"
        f"Channel 분포: "
        f"{dict(channel_counter)}\n"
        f"상위 Issue Category: "
        f"{category_counter.most_common(5)}"
    )

    sample_vocs = [
        (
            f"{row['voc_id']} | "
            f"{row['product_line']} | "
            f"{row['issue_category']} | "
            f"{row['severity']} | "
            f"만족도 {row['satisfaction_score']} | "
            f"해결 {row['resolution_hours']}h | "
            f"반복문의 {row['repeat_contact']} | "
            f"{row['customer_text']}"
        )
        for row in filtered[:5]
    ]

    policy_evidence = []

    for row in POLICY_ROWS:

        if (
            product_filter
            and
            row["product_line"] != product_filter
        ):
            continue

        if (
            category_filter
            and
            row["issue_category"] != category_filter
        ):
            continue

        policy_evidence.append(
            (
                f"{row['policy_id']} | "
                f"{row['product_line']} | "
                f"{row['issue_category']} | "
                f"SLA {row['response_sla_hours']}h | "
                f"Escalation "
                f"{row['escalation_required']} | "
                f"{row['policy_summary']}"
            )
        )

        if len(policy_evidence) >= 5:
            break

    return {
        "product_filter":
            product_filter,
        "category_filter":
            category_filter,
        "evidence_summary":
            evidence_summary,
        "sample_vocs":
            sample_vocs,
        "policy_evidence":
            policy_evidence,
    }


RESEARCH_AGENT_PROMPT = '''
당신은 고객 VOC Research Agent입니다.

제공된 Python Evidence만으로 분석하세요.

수치를 임의로 바꾸거나 만들지 마세요.

반복 문의율, 만족도, 해결시간,
Severity, Issue Category를 함께 해석하세요.

정책 Evidence가 있으면 개선 방향에 반영하세요.

상관관계를 확정적 인과관계처럼 말하지 마세요.
'''


def research_agent_node(
    state: VOCMultiAgentState
):

    evidence = build_evidence(
        state["question"]
    )

    result = research_model.invoke(
        [
            SystemMessage(
                content=RESEARCH_AGENT_PROMPT
            ),
            HumanMessage(
                content=f'''
사용자 질문:

{state["question"]}


Router 작업:

{state["routed_task"]}


대상:

{state["audience"]}


VOC Evidence:

{evidence["evidence_summary"]}


대표 VOC:

{json.dumps(
    evidence["sample_vocs"],
    ensure_ascii=False,
    indent=2
)}


서비스 정책 Evidence:

{json.dumps(
    evidence["policy_evidence"],
    ensure_ascii=False,
    indent=2
)}


이 Evidence만으로 분석하세요.
'''
            ),
        ]
    )

    final_answer = ""

    if not state["needs_writing"]:

        final_answer = (
            result.summary
            + "\n\n[핵심 결과]\n- "
            + "\n- ".join(result.key_findings)
            + "\n\n[위험 포인트]\n- "
            + "\n- ".join(result.risk_points)
            + "\n\n[권장 조치]\n- "
            + "\n- ".join(result.recommended_actions)
        )

    return {
        "product_filter":
            evidence["product_filter"],
        "category_filter":
            evidence["category_filter"],
        "evidence_summary":
            evidence["evidence_summary"],
        "sample_vocs":
            evidence["sample_vocs"],
        "policy_evidence":
            evidence["policy_evidence"],
        "research_summary":
            result.summary,
        "key_findings":
            result.key_findings,
        "risk_points":
            result.risk_points,
        "recommended_actions":
            result.recommended_actions,
        "recommended_structure":
            result.recommended_structure,
        "active_agent":
            "research_agent",
        "execution_order": [
            *state.get(
                "execution_order",
                [],
            ),
            "research_agent",
        ],
        "final_answer":
            final_answer,
    }


def route_after_research(
    state: VOCMultiAgentState
) -> Literal[
    "writer_agent",
    "end",
]:

    if state["needs_writing"]:
        return "writer_agent"

    return "end"


WRITER_AGENT_PROMPT = '''
당신은 VOC Writer Agent입니다.

Research Agent가 이미 실제 데이터를 분석했습니다.

Research 결과만으로
사용자가 바로 쓸 수 있는 완성 결과물을 작성하세요.

새 수치를 만들지 마세요.

manager는 핵심 지표, 위험, Action Item 중심으로 작성하세요.

instructor는 분석 과정과 교육 포인트를 포함하세요.
'''


def writer_agent_node(
    state: VOCMultiAgentState
):

    research_package = {
        "summary":
            state["research_summary"],
        "key_findings":
            state["key_findings"],
        "risk_points":
            state["risk_points"],
        "recommended_actions":
            state["recommended_actions"],
        "recommended_structure":
            state["recommended_structure"],
    }

    response = model.invoke(
        [
            SystemMessage(
                content=WRITER_AGENT_PROMPT
            ),
            HumanMessage(
                content=f'''
원래 질문:

{state["question"]}


대상:

{state["audience"]}


Research 결과:

{json.dumps(
    research_package,
    ensure_ascii=False,
    indent=2
)}


Evidence Summary:

{state["evidence_summary"]}


완성된 결과물을 작성하세요.
'''
            ),
        ]
    )

    return {
        "final_answer":
            get_response_text(response),
        "active_agent":
            "writer_agent",
        "execution_order": [
            *state.get(
                "execution_order",
                [],
            ),
            "writer_agent",
        ],
    }


EXPLAINER_AGENT_PROMPT = '''
당신은 VOC 분석 개념 Explainer Agent입니다.

실제 VOC CSV를 분석하지 않습니다.

[정의]
[왜 중요한가]
[VOC 분석에서 어떻게 보는가]
[간단한 예]

순서로 설명하세요.
'''


def explainer_agent_node(
    state: VOCMultiAgentState
):

    response = model.invoke(
        [
            SystemMessage(
                content=
                    EXPLAINER_AGENT_PROMPT
            ),
            HumanMessage(
                content=f'''
질문:

{state["question"]}


대상 수준:

{state["audience"]}


개념을 이해하기 쉽게 설명하세요.
'''
            ),
        ]
    )

    return {
        "final_answer":
            get_response_text(response),
        "active_agent":
            "explainer_agent",
        "execution_order": [
            *state.get(
                "execution_order",
                [],
            ),
            "explainer_agent",
        ],
    }


builder = StateGraph(
    VOCMultiAgentState
)

builder.add_node(
    "router",
    router_node,
)

builder.add_node(
    "research_agent",
    research_agent_node,
)

builder.add_node(
    "writer_agent",
    writer_agent_node,
)

builder.add_node(
    "explainer_agent",
    explainer_agent_node,
)

builder.add_edge(
    START,
    "router",
)

builder.add_conditional_edges(
    "research_agent",
    route_after_research,
    {
        "writer_agent":
            "writer_agent",
        "end":
            END,
    },
)

builder.add_edge(
    "writer_agent",
    END,
)

builder.add_edge(
    "explainer_agent",
    END,
)


multi_agent_graph = (
    builder.compile()
)


def run_multi_agent(
    question: str,
    audience: str,
    expected_flow: str,
):

    initial_state = {
        "question":
            question,
        "audience":
            audience,
        "selected_agent":
            "",
        "route_reason":
            "",
        "route_confidence":
            0,
        "routed_task":
            "",
        "needs_writing":
            False,
        "product_filter":
            "",
        "category_filter":
            "",
        "evidence_summary":
            "",
        "sample_vocs":
            [],
        "policy_evidence":
            [],
        "research_summary":
            "",
        "key_findings":
            [],
        "risk_points":
            [],
        "recommended_actions":
            [],
        "recommended_structure":
            [],
        "active_agent":
            "",
        "execution_order":
            [],
        "final_answer":
            "",
    }

    result = multi_agent_graph.invoke(
        initial_state,
        config={
            "recursion_limit": 10
        },
    )

    print("\n" + "=" * 80)
    print("Routing Summary")
    print("=" * 80)

    print("\nExpected Flow:")
    print(expected_flow)

    print("\nSelected Agent:")
    print(result["selected_agent"])

    print("\nConfidence:")
    print(result["route_confidence"])

    print("\nRoute Reason:")
    print(result["route_reason"])

    print("\nNeeds Writing:")
    print(result["needs_writing"])

    print("\nExecution Order:")
    print(
        " -> ".join(result["execution_order"])
    )

    if result["evidence_summary"]:

        print("\n" + "=" * 80)
        print("Evidence Summary")
        print("=" * 80)

        print(
            result["evidence_summary"]
        )

    print("\n" + "=" * 80)
    print("Final Answer")
    print("=" * 80)

    print(
        result["final_answer"]
    )

    return result


TEST_CASES = [
    {
        "name":
            "VOC Analysis Only",
        "question": (
            "SmartHome Hub의 연결 오류 VOC를 분석해서 "
            "반복 문의와 해결시간 측면의 핵심 문제를 정리해줘. "
            "보고서는 아직 만들지 마."
        ),
        "audience":
            "intermediate",
        "expected_flow":
            "router -> research_agent",
    },
    {
        "name":
            "Manager Report",
        "question": (
            "AirPure Pro의 초기 불량 VOC를 분석하고 "
            "관리자 회의에서 바로 사용할 수 있는 "
            "개선 보고서 형태로 작성해줘."
        ),
        "audience":
            "manager",
        "expected_flow":
            "router -> research_agent -> writer_agent",
    },
    {
        "name":
            "VOC Concept Explanation",
        "question": (
            "VOC에서 반복 문의율이 왜 중요한 지표인지 "
            "초보자도 이해할 수 있게 설명해줘."
        ),
        "audience":
            "beginner",
        "expected_flow":
            "router -> explainer_agent",
    },
]


RUN_ALL_EXAMPLES = True
DEFAULT_EXAMPLE_INDEX = 0


if __name__ == "__main__":

    if RUN_ALL_EXAMPLES:

        for test in TEST_CASES:

            print("\n" + "#" * 80)
            print(test["name"])
            print("#" * 80)

            run_multi_agent(
                question=
                    test["question"],
                audience=
                    test["audience"],
                expected_flow=
                    test["expected_flow"],
            )

    else:

        test = (
            TEST_CASES[
                DEFAULT_EXAMPLE_INDEX
            ]
        )

        run_multi_agent(
            question=
                test["question"],
            audience=
                test["audience"],
            expected_flow=
                test["expected_flow"],
        )
