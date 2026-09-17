# ============================================================
# Multi-Agent - Agent별 Tool Permission
#
# 핵심 목표
# - Research Agent: search_internal_knowledge, get_teaching_example
# - Writer Agent: Tool 없음
# - Reviewer Agent: verify_concept_reference, get_review_checklist
#
# Agent Role + Context + Tool Permission을 각각 분리한다.
# ============================================================

# ============================================================
# 1. Import
# ============================================================

import json
import os
import re
from operator import add
from typing import Annotated, Literal, TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

# ============================================================
# 2. 환경 변수
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

# ============================================================
# GEMINI_API_KEY만 사용
# ============================================================

os.environ.pop("GOOGLE_API_KEY", None)
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY가 없습니다.\n\n"
        ".env 파일에 다음과 같이 입력하세요.\n\n"
        "GEMINI_API_KEY=...\n"
        "GEMINI_MODEL=gemini-3.7-flash"
    )
print("GEMINI_API_KEY:", "LOADED")
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

# ============================================================
# 3. Gemini Model
# ============================================================

base_model = (
    ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        vertexai=False,
        temperature=0,
        max_retries=2,
    )
)

# ============================================================
# 4. 내부 Knowledge Base
# ============================================================

INTERNAL_DOCUMENTS = [
    {
        "doc_id": "DOC-001",
        "title": "Router Pattern",
        "keywords": ["router", "routing", "라우터", "분류"],
        "content": (
            "Router Pattern은 사용자 요청을 먼저 분석하고 "
            "가장 적합한 전문 Agent 또는 처리 경로를 선택하는 "
            "Multi-Agent 구조다. 일반적으로 입구에서 요청을 "
            "분류하는 Dispatch 역할에 적합하다."
        ),
    },
    {
        "doc_id": "DOC-002",
        "title": "Handoff Pattern",
        "keywords": ["handoff", "핸드오프", "제어권"],
        "content": (
            "Handoff는 현재 작업 중인 Agent가 자신의 작업을 "
            "마친 뒤 다른 Agent에게 실행 제어권과 필요한 "
            "Context를 넘기는 Multi-Agent 패턴이다."
        ),
    },
    {
        "doc_id": "DOC-003",
        "title": "Supervisor Pattern",
        "keywords": ["supervisor", "수퍼바이저", "감독", "worker"],
        "content": (
            "Supervisor Pattern은 중앙 Supervisor가 Worker의 "
            "작업 결과를 다시 확인하면서 다음 Worker를 "
            "반복적으로 선택하고 전체 작업을 조정하는 구조다."
        ),
    },
    {
        "doc_id": "DOC-004",
        "title": "Shared State",
        "keywords": ["shared state", "state", "공유 상태"],
        "content": (
            "Shared State는 Multi-Agent Workflow에서 여러 "
            "Node와 Agent가 작업 진행 상황과 결과를 공유할 수 "
            "있도록 하는 공통 상태 공간이다."
        ),
    },
    {
        "doc_id": "DOC-005",
        "title": "Context Isolation",
        "keywords": ["context isolation", "context", "컨텍스트", "격리"],
        "content": (
            "Context Isolation은 각 Agent에게 전체 State를 "
            "무조건 전달하는 대신 해당 Agent의 역할에 필요한 "
            "정보만 제공하는 설계 방식이다. 불필요한 Context와 "
            "역할 간 간섭을 줄일 수 있다."
        ),
    },
    {
        "doc_id": "DOC-006",
        "title": "Tool Permission",
        "keywords": ["tool permission", "tool", "권한", "도구"],
        "content": (
            "Agent별 Tool Permission은 각 Agent에게 자신의 "
            "역할에 필요한 Tool만 제공하는 방식이다. "
            "Research Agent에는 검색 Tool을, Reviewer에는 "
            "검증 Tool을 제공하고 Writer에는 Tool을 주지 않는 "
            "구조를 사용할 수 있다."
        ),
    },
    {
        "doc_id": "DOC-007",
        "title": "ToolNode",
        "keywords": ["toolnode", "tool node", "도구 노드"],
        "content": (
            "ToolNode는 AIMessage의 tool_calls를 읽어 실제 "
            "Tool을 실행하고 Tool 결과를 ToolMessage로 "
            "변환하는 LangGraph의 실행 Node다."
        ),
    },
    {
        "doc_id": "DOC-008",
        "title": "Sequential Tool Calling",
        "keywords": ["sequential", "순차", "tool calling"],
        "content": (
            "Sequential Tool Calling은 첫 Tool의 결과가 "
            "다음 Tool의 입력에 필요한 경우 Tool을 순차적으로 "
            "실행하는 방식이다."
        ),
    },
    {
        "doc_id": "DOC-009",
        "title": "Parallel Tool Calling",
        "keywords": ["parallel", "병렬", "tool calling"],
        "content": (
            "서로 입력과 결과에 의존하지 않는 Tool은 모델이 "
            "동시에 여러 Tool Call을 생성할 수 있으며 실행 "
            "환경에서 병렬 처리할 수 있다."
        ),
    },
    {
        "doc_id": "DOC-010",
        "title": "Reflection",
        "keywords": ["reflection", "critique", "revision", "리플렉션"],
        "content": (
            "Reflection은 생성된 답변을 Critique하고 문제를 "
            "발견하면 Revision한 뒤 다시 평가하는 품질 개선 "
            "Loop를 구성하는 패턴이다."
        ),
    },
    {
        "doc_id": "DOC-011",
        "title": "Supervisor vs Reflection",
        "keywords": ["supervisor", "reflection", "비교"],
        "content": (
            "Reflection은 결과 자체를 평가하고 수정하는 "
            "Self-Correction 구조에 가깝고, Supervisor는 "
            "여러 전문 Worker의 작업을 조정하는 Multi-Agent "
            "Orchestration 구조라는 차이가 있다."
        ),
    },
    {
        "doc_id": "DOC-012",
        "title": "ToolRuntime",
        "keywords": ["toolruntime", "runtime", "state", "context", "store"],
        "content": (
            "ToolRuntime은 Tool 내부에서 현재 State, Context, "
            "Store와 실행 관련 정보에 접근할 수 있도록 한다."
        ),
    },
    {
        "doc_id": "DOC-013",
        "title": "Agent Tool Isolation",
        "keywords": ["tool isolation", "tool permission", "least privilege", "최소 권한"],
        "content": (
            "Multi-Agent 시스템에서는 각 Agent에게 업무에 "
            "필요한 최소 Tool만 노출하면 Tool 선택 혼란을 줄이고 "
            "역할 경계를 명확하게 유지하는 데 도움이 된다."
        ),
    },
    {
        "doc_id": "DOC-014",
        "title": "Writer Agent",
        "keywords": ["writer", "writer agent", "작성"],
        "content": (
            "Writer Agent는 Research 결과와 사용자 요구를 "
            "바탕으로 최종 설명, 문서 또는 발표문을 작성한다. "
            "작성 역할만 필요하다면 외부 검색 Tool을 반드시 "
            "가질 필요는 없다."
        ),
    },
    {
        "doc_id": "DOC-015",
        "title": "Reviewer Agent",
        "keywords": ["reviewer", "review", "검토", "검증"],
        "content": (
            "Reviewer Agent는 Draft의 정확성, 질문 대응 여부, "
            "누락, 근거 일치 여부와 대상 수준 적합성 등을 "
            "검토한다."
        ),
    },
]

# ============================================================
# 5. 수업 예제 데이터
# ============================================================

TEACHING_EXAMPLES = {
    "router": (
        "사용자가 'RAG가 뭐야?'라고 질문하면 Explainer로, "
        "'RAG 장단점을 조사해줘'라고 하면 Research로, "
        "'RAG 강의 대본을 작성해줘'라고 하면 Writer로 "
        "보내는 구조를 Router 예제로 사용할 수 있다."
    ),
    "handoff": (
        "Research Agent가 조사를 완료한 뒤 "
        "'이제 설명문 작성이 필요하다'고 판단하여 "
        "Writer Agent에게 제어권을 넘기는 흐름이 "
        "Handoff의 대표적인 예다."
    ),
    "supervisor": (
        "팀장인 Supervisor가 Research에게 조사시키고, "
        "Writer에게 작성시키고, Reviewer에게 검토시킨 뒤 "
        "문제가 있으면 다시 Writer에게 수정시키는 흐름으로 "
        "설명할 수 있다."
    ),
    "context_isolation": (
        "회사에서 연구원에게 편집자의 내부 업무 메모까지 "
        "전부 보여줄 필요가 없는 것처럼 Agent에게도 "
        "업무에 필요한 Context만 제공한다고 설명할 수 있다."
    ),
    "tool_permission": (
        "연구원에게 검색 시스템을, 검수자에게 검증 시스템을 "
        "제공하고 작성자에게는 작성 업무만 맡기는 회사의 "
        "권한 분리와 비슷하다고 설명할 수 있다."
    ),
    "reflection": (
        "학생이 답안을 작성하고 선생님이 피드백하고, "
        "학생이 수정한 뒤 다시 검토받는 과정을 "
        "Reflection Loop에 비유할 수 있다."
    ),
}

# ============================================================
# 6. Reviewer Reference
# ============================================================
#
# Reviewer는 검색 DB를 직접 사용하지 않는다.
#
# 검증을 위해 제한된 Reference Tool만 사용할 수 있다.
#
# ============================================================

REFERENCE_FACTS = {
    "router": (
        "Router는 요청의 목적을 분류하여 적합한 Agent나 "
        "경로로 Dispatch하는 역할이다."
    ),
    "handoff": (
        "Handoff는 현재 Agent가 작업 도중 다른 Agent에게 "
        "제어권을 넘기는 패턴이다."
    ),
    "supervisor": (
        "Supervisor는 Worker 결과를 다시 받고 다음 작업을 "
        "반복적으로 결정할 수 있는 중앙 Orchestrator다."
    ),
    "shared_state": (
        "Shared State는 여러 Agent 또는 Node가 작업 결과와 "
        "상태를 공유하는 공통 상태 공간이다."
    ),
    "context_isolation": (
        "Context Isolation은 Agent에게 필요한 Context만 "
        "제공하는 것이며 Agent끼리 모든 정보 공유를 "
        "금지한다는 의미는 아니다."
    ),
    "tool_permission": (
        "Agent별 Tool Permission은 역할에 필요한 Tool만 "
        "노출하여 권한과 책임을 분리하는 설계 방식이다."
    ),
    "reflection": (
        "Reflection은 결과를 Critique하고 Revision한 뒤 "
        "재평가하는 반복 품질 개선 방식이다."
    ),
    "toolnode": (
        "ToolNode는 모델의 tool_calls를 실행하고 결과를 "
        "ToolMessage 형태로 반환한다."
    ),
}

# ============================================================
# 7. Research Tool 1
#
# 내부 Knowledge Search
# ============================================================

@tool
def search_internal_knowledge(query: str, top_k: int = 3) -> dict:

    '''
    Multi-Agent와 Agent 교육용 내부 Knowledge Base 검색한다.

    Router, Handoff, Supervisor, Shared State, Context Isolation, Tool Permission,
    Reflection, ToolRunTime 등의 기술 내용을 조사할 때 사용한다.
    '''

    print("\n")
    print("=" * 70)
    print("RESEARCH TOOL")
    print("search_internal_knowledge")
    print("=" * 70)
    print("query:", query)
    print("top_k:", top_k)

    top_k = max(1, min(int(top_k), 5))
    query_lower = query.lower()

    tokens = [token.lower() for token in re.findall('[A-Za-z0-9가-힣_]+', query) if len(token) >= 2]

    scored_documents = []

    for document in INTERNAL_DOCUMENTS:
        score = 0
        for keyword in document['keywords']:
            if keyword.lower() in query_lower:
                score += 5

        searchable_text = (document['title'] + ' ' + document['content']).lower()
        for token in tokens:
            if token in searchable_text:
                score += 1

        scored_documents.append((score, document))

    scored_documents.sort(
        key=lambda item: item[0],
        reverse=True
    )

    results = []
    for score, document in scored_documents[:top_k]:
        results.append(
            {
                'doc_id': document['doc_id'],
                'title': document['title'],
                'match_score': score,
                'content': document['content']
            }
        )
    
    print()
    print("[SEARCH RESULT]")
    for result in results:
        print(result["doc_id"], result["title"], "score=", result["match_score"])
    return {"query": query, "results": results}

# ============================================================
# 8. Research Tool 2
#
# 수업용 Example
# ============================================================

TeachingTopic = Literal[
    "router",
    "handoff",
    "supervisor",
    "context_isolation",
    "tool_permission",
    "reflection",
]

@tool
def get_teaching_example(topic: TeachingTopic) -> dict:
    '''
    특정 Agent 개념을 학생에게 설명할 때 사용할 교육용 비유 또는
    실습 예제를 가져온다.
    '''

    print("\n")
    print("=" * 70)
    print("RESEARCH TOOL")
    print("get_teaching_example")
    print("=" * 70)
    print("topic:", topic)

    return {
        'topic': topic,
        'example': TEACHING_EXAMPLES[topic]
    }


# ============================================================
# 9. Reviewer Tool 1
#
# 개념 Reference 검증
# ============================================================

ReferenceConcept = Literal[
    "router",
    "handoff",
    "supervisor",
    "shared_state",
    "context_isolation",
    "tool_permission",
    "reflection",
    "toolnode",
]

@tool
def verify_concept_reference(concept: ReferenceConcept) -> dict:

    '''
    Reviewer가 Draft의 Agent 관련 개념이 맞는지 검증할 때 사용할 기준 Reference를 반환한다.

    일반적인 조사나 자료 검색 Tool이 아니다. Reviewer 전용 검증 Tool이다.
    '''
    print("\n")
    print("=" * 70)
    print("REVIEWER TOOL")
    print("verify_concept_reference")
    print("=" * 70)
    print("concept:", concept)

    return {
        'concept': concept,
        'reference': REFERENCE_FACTS[concept]
    }


# ============================================================
# 10. Reviewer Tool 2
#
# Quality Checklist
# ============================================================

ReviewAudience = Literal["beginner", "intermediate", "instructor"]

@tool
def get_review_checklist(audience: ReviewAudience) -> dict:

    '''
    Reviewer가 Draft를 검토할 때 사용할 Audience별 품질 Checklist를 반환한다.

    Writer용 Tool이 아니다.
    '''

    print("\n")
    print("=" * 70)
    print("REVIEWER TOOL")
    print("get_review_checklist")
    print("=" * 70)
    checklists = {
        "beginner": [
            "전문 용어를 바로 풀어서 설명했는가?",
            "쉬운 예 또는 비유가 있는가?",
            "설명이 지나치게 복잡하지 않은가?",
            "질문의 핵심에 직접 답했는가?",
        ],
        "intermediate": [
            "핵심 기술 용어를 정확하게 사용했는가?",
            "개념 차이를 명확하게 구분했는가?",
            "Workflow 또는 동작 구조를 설명했는가?",
            "근거 없는 기술적 주장을 추가하지 않았는가?",
        ],
        "instructor": [
            "강사가 학생에게 설명하기 좋은 구조인가?",
            "학생이 혼동할 포인트를 구분했는가?",
            "예제 또는 비교 포인트가 포함되었는가?",
            "핵심 개념의 정의가 정확한가?",
            "수업 흐름으로 재사용하기 쉬운가?",
        ],
    }

    return {
        'audience': audience,
        'checklist': checklists[audience]
    }



# ============================================================
# 11. Agent별 Tool Permission
# ============================================================

RESEARCH_TOOLS = [search_internal_knowledge, get_teaching_example]

REVIEWER_TOOLS = [verify_concept_reference, get_review_checklist]

WRITER_TOOLS = []


# ============================================================
# 12. Tool Permission 출력
# ============================================================

def print_tool_permissions():
    print("\n")
    print("#" * 70)
    print("AGENT TOOL PERMISSIONS")
    print("#" * 70)
    print()
    print("[Research Agent]")
    for tool_object in RESEARCH_TOOLS:
        print("-", tool_object.name)
    print()
    print("[Writer Agent]")
    if not WRITER_TOOLS:
        print("- Tool 없음")
    print()
    print("[Reviewer Agent]")
    for tool_object in REVIEWER_TOOLS:
        print("-", tool_object.name)

# ============================================================
# 13. Agent별 Model Binding
# ============================================================
# Research Model
#
# search_internal_knowledge
# get_teaching_example
# 만 알고 있다.
#
#
# Reviewer Model
#
# verify_concept_reference
# get_review_checklist
# 만 알고 있다.
#
#
# Writer Model
# bind_tools() 자체를 하지 않는다.
#
# ============================================================


research_model_with_tools = base_model.bind_tools(RESEARCH_TOOLS)
reviewer_model_with_tools = base_model.bind_tools(REVIEWER_TOOLS)
writer_model = base_model

# ============================================================
# 14. Reviewer 최종 평가 Schema
# ============================================================

class ReviewResult(
    BaseModel
):
    passed: bool = Field(
        description="현재 Draft가 사용자에게 제공 가능한 수준인지 여부"
    )

    score: int = Field(
        ge=0,
        le=100
    )

    issues: list[str]

    feedback: str

    revision_instructions: list[str]

review_evaluator = base_model.with_structured_output(ReviewResult)

# ============================================================
# 15. Supervisor Decision
# ============================================================

class SupervisorDecision(BaseModel):

    request_type: Literal[
        'research_only',
        'explain',
        'write',
        'review_only',
        'review_and_fix'
    ]

    next_agent: Literal[
        'research_agent',
        'writer_agent',
        'reviewer_agent'
    ]

    reason: str

    task_for_agent: str


supervisor_model = base_model.with_structured_output(SupervisorDecision)

# ============================================================
# 16. State
# ============================================================
#
# Research Tool Conversation
# Reviewer Tool Conversation
#
# 을 별도 Message Channel로 관리한다.
#
#
# research_messages
# reviewer_messages
#
#
# add_messages Reducer를 사용한다.
#
# ============================================================

class MultiAgentState(TypedDict):
    # --------------------------------------------------------
    # 사용자
    # --------------------------------------------------------
    question: str
    audience: str
    # --------------------------------------------------------
    # Supervisor
    # --------------------------------------------------------
    request_type: str
    supervisor_round: int
    delegated_task: str
    supervisor_reason: str
    # --------------------------------------------------------
    # Research
    # --------------------------------------------------------
    research_done: bool
    research_summary: str
    research_evidence: list[str]
    research_messages: Annotated[list[BaseMessage], add_messages]
    # --------------------------------------------------------
    # Writer
    # --------------------------------------------------------
    writer_done: bool
    draft_answer: str
    revision_count: int
    # --------------------------------------------------------
    # Reviewer
    # --------------------------------------------------------
    review_done: bool
    review_in_progress: bool
    review_passed: bool
    review_score: int
    review_feedback: str
    review_issues: list[str]
    revision_instructions: list[str]
    reviewer_messages: Annotated[list[BaseMessage], add_messages]
    # --------------------------------------------------------
    # Trace
    # --------------------------------------------------------
    execution_order: Annotated[list[str], add]
    route_history: Annotated[list[dict], add]
    tool_audit: Annotated[list[dict], add]
    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------
    final_answer: str

# ============================================================
# 17. 설정
# ============================================================

MAX_SUPERVISOR_ROUNDS = 8

MAX_WRITER_REVISIONS = 2

MIN_REVIEW_SCORE = 85

# ============================================================
# 18. Text 추출
# ============================================================

def get_ai_text(message):
    text = getattr(message, "text", None)
    if isinstance(text, str) and text:
        return text
    if isinstance(message.content, str):
        return message.content
    return str(message.content)

# ============================================================
# 19. 최근 Human 이후 ToolMessage 추출
# ============================================================

def get_current_cycle_tool_messages(messages):
    start_index = -1
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            start_index = index
            break

    if start_index == -1:
        return []

    return [
        message
        for message in messages[start_index + 1:]
        if isinstance(message, ToolMessage)
    ]

# ============================================================
# 20. Tool 이름 추출
# ============================================================

def get_trailing_tool_names(messages):
    names = []
    for message in reversed(messages):
        if not isinstance(message, ToolMessage):
            break
        if message.name:
            names.append(message.name)
    names.reverse()
    return names

# ============================================================
# 21. Research Agent Prompt
# ============================================================

RESEARCH_SYSTEM_PROMPT = """
당신은 Multi-Agent 시스템의 Research Agent입니다.

당신에게 허용된 Tool:

1. search_internal_knowledge
2. get_teaching_example



============================================================
역할
============================================================

당신은 조사와 자료 수집에 집중합니다.

내부 Agent 교육 자료에서 정보를 찾으려면:
search_internal_knowledge를 사용합니다.


학생에게 설명 할 수 있는 예나 비유가 필요하면:
get_teaching_example을 사용합니다.



============================================================
Tool Permission
============================================================

당신은 Reviewer 전용 Tool을 사용할 수 없습니다.
다음 Tool은 당신의 Tool이 아닙니다.

verify_concept_reference
get_review_checklist

Writer 작업도 수행하지 마세요.



============================================================
중요
============================================================

기술적인 조사 요청이라면 최소 하나의 Reseach Tool을 사용한 뒤
Evidence를 바탕으로 조사 결과를 작성하세요.

Tool 결과를 받았다면 같은 검색을 불필요하게 반복하지 마세요.
"""

# ============================================================
# 22. Research Agent
# ============================================================

def research_agent_node(state: MultiAgentState):
    print("\n")
    print("=" * 70)
    print("AGENT")
    print("Research Agent")
    print("=" * 70)
    messages = state.get("research_messages", [])
    tool_messages = get_current_cycle_tool_messages(messages)
    # ========================================================
    # CASE 1
    #
    # Research 시작
    # ========================================================
    if not messages:
        human_message = (
            HumanMessage(
                content=(
                    f"""
사용자 질문:

{state["question"]}


대상:

{state["audience"]}


Supervisor가 위임한 작업:

{state.get("delegated_task", "")}


필요한 내부 자료를 Tool로 조사하세요.

기술 설명에 예시가 필요하면 교육용 Example Tool도 사용할 수 있습니다.
"""
                )
            )
        )
        response = (
            research_model_with_tools.invoke(
                [
                    SystemMessage(
                        content=RESEARCH_SYSTEM_PROMPT
                    ),
                    human_message
                ]
            )
        )
        print()
        print("[RESEARCH TOOL CALLS]")
        print(response.tool_calls)
        # ====================================================
        # Tool Call 발생
        # ====================================================
        if response.tool_calls:
            return {
                'research_messages': [human_message, response],
                'execution_order': ['research_agent']
            }
        # ====================================================
        # 모델이 Tool을 호출하지 않은 경우
        #
        # 해당 응답을 조사 결과로 사용
        # ====================================================
        direct_text = get_ai_text(response)

        return {
            'research_done': True,
            'research_summary': direct_text,
            'research_envidence': [],
            'research_messages': [human_message, response],
            'execution_order': ['research_agent']
        }

    # ========================================================
    # CASE 2
    #
    # Tool Evidence가 있음
    #
    # 조사 결과 Synthesizing
    # ========================================================
    if tool_messages:
        evidence = [
            {
                'tool': message.name,
                'content': str(message.content)
            }
            for message in tool_messages
        ]  

        print('\n[RESEARCH EVIDENCE]')
        print(
            json.dumps(
                evidence,
                ensure_ascii=False,
                indent=2
            )
        )

        synthesis_prompt = f"""
당신은 Research Agent입니다.

다음 Tool Evidence를 이용하여 Supervisor와 Writer가 사용할 조사 결과를 작성하세요.


사용자 질문:

{state["question"]}


Tool Evidence:

{
    json.dumps(
        evidence,
        ensure_ascii=False,
        indent=2
    )
}


다음 구조로 정리하세요.

[조사 요약]

[핵심 Findings]

[주의할 점]

Tool Evidence에 없는 구체적인 사실은 새로 만들지 마세요.
"""

        response = base_model.invoke(
            [
                SystemMessage(
                    content='당신은 조사 결과를 Evidence 기반으로 정리하는 Research Agent입니다.'
                ),
                HumanMessage(
                    content=synthesis_prompt
                )
            ]
        )
                
        summary = get_ai_text(response)
        print()
        print("[RESEARCH RESULT]")
        print(summary)
        return {
            "research_done": True,
            "research_summary": summary,
            "research_evidence": [
                json.dumps(
                    item,
                    ensure_ascii=False
                ) for item in evidence
            ],
            "research_messages": [response],
            "execution_order": ["research_agent"],
        }
    # ========================================================
    # 예상하지 못한 상태
    # ========================================================

    return {
        'research_done': True,
        'research_summary': 'Research Tool Evidence를 확보하지 못했습니다.',
        'research_evidence': [],
        'execution_order': ['research_agent']
    }


# ============================================================
# 23. Research Agent Router
# ============================================================

def route_after_research_agent(state: MultiAgentState):
    messages = state.get('research_messages', [])

    if messages:
        last_message = messages[-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return 'research_tools'

    if state.get('research_done', False):
        return 'supervisor'

    return 'supervisor'

# ============================================================
# 24. Research Tool 결과 Audit
# ============================================================

def inspect_research_tools_node(state: MultiAgentState):

    names = get_trailing_tool_names(
        state.get('research_messages', [])
    )

    print('\n[RESEARCH TOOL AUDIT]')
    print(names)

    return {
        'tool_audit': [
            {
                'agent': 'research_agent',
                'allowed_tools': [
                    tool_object.name
                    for tool_object in RESEARCH_TOOLS
                ],
                'executed_tools': names
            }
        ],
        'execution_order': ['research_tools']
    }


# ============================================================
# 25. Writer Prompt
# ============================================================

WRITER_SYSTEM_PROMPT = """
당신은 Multi-Agent 시스템의 Writer Agent입니다.

당신에게는 Tool이 없습니다.

Research Agent가 이미 확보한 Evidence와 Supervisor가 전달한
작업만 이용해서 사용자용 Draft를 작성합니다.


============================================================
중요
============================================================

직접 새로운 내부 자료를 검색할 수 없습니다.

검색이 필요해 보인다고 해서 존재하지 않는 Tool을 호출하려 하지 마세요.

Research 결과 있으면 적극적으로 활용하세요.

Reviewer 수정 지시가 있으면 반드시 반영하세요.
"""

# ============================================================
# 26. Writer Agent
# ============================================================

def writer_agent_node(state: MultiAgentState):
    print("\n")
    print("=" * 70)
    print("AGENT")
    print("Writer Agent")
    print("=" * 70)
    print()
    print("[WRITER TOOL PERMISSION]")
    print("Tool 없음")
    previous_draft = state.get("draft_answer", "")
    review_issues = state.get("review_issues", [])
    revision_instructions = state.get("revision_instructions", [])
    is_revision = bool(previous_draft and review_issues)
    prompt = f"""
사용자의 질문:

{state["question"]}


Audience:

{state["audience"]}


Supervisor Task:

{state.get("delegated_task", "")}


============================================================
RESEARCH RESULT
============================================================

{state.get("research_summary", "")}


============================================================
RESEARCH EVIDENCE
============================================================

{
    json.dumps(
        state.get("research_evidence", []),
        ensure_ascii=False,
        indent=2,
    )
}


============================================================
PREVIOUS DRAFT
============================================================

{previous_draft}


============================================================
REVIEW ISSUES
============================================================

{
    json.dumps(
        review_issues,
        ensure_ascii=False,
        indent=2,
    )
}


============================================================
REVISION INSTRUCTIONS
============================================================

{
    json.dumps(
        revision_instructions,
        ensure_ascii=False,
        indent=2,
    )
}


사용자에게 제공할 최종 Draft를 작성하세요.

Research Evidence에 없는 내부 사실을
새로 만들어내지 마세요.
"""
    response = (
        writer_model.invoke(
            [
                SystemMessage(content=WRITER_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
    )
    text = get_ai_text(response)
    print()
    print("[WRITER DRAFT]")
    print(text)
    revision_count = state.get("revision_count", 0)
    if is_revision:
        revision_count += 1
    return {
        "writer_done": True,
        "draft_answer": text,
        "revision_count": revision_count,
        # ----------------------------------------------------
        # 새 Draft가 생겼으므로 Review Reset
        # ----------------------------------------------------
        "review_done": False,
        "review_in_progress": False,
        "review_passed": False,
        "review_score": 0,
        "review_feedback": "",
        "review_issues": [],
        "revision_instructions": [],
        "final_answer": text,
        "tool_audit": [{"agent": "writer_agent", "allowed_tools": [], "executed_tools": []}],
        "execution_order": ["writer_agent"],
    }

# ============================================================
# 27. Reviewer Tool Agent Prompt
# ============================================================

REVIEWER_TOOL_SYSTEM_PROMPT = """
당신은 Multi-Agent 시스템의 Reviewer Agent입니다.

당신에게 허용된 Tool:

1. verify_concept_reference
2. get_review_checklist


============================================================
역할
============================================================

Draft의 개념이 정확한지 확인하려면:

verify_concept_reference를 사용하세요


Audience에 적합한 글인지 확인하려면:

get_review_checklist를 사용할 수 있습니다.


============================================================
Tool Permission
============================================================

당신은 Research Agent의 Tool을 사용할 수 없습니다.

사용할 수 없는 Tool:

search_internal_knowledge
get_teaching_example


당신의 역할은 새로운 자료 조사가 아니라 현재 Draft의 검증입니다.


============================================================
중요
============================================================

최소 하나의 Reviewer Tool을 사용하여 검증 근거를 확보하세요.

필요하면 서로 다른 개념에 대해 여러 verify_concept_reference Tool을
호출할 수 있습니다.
"""

# ============================================================
# 28. Reviewer Agent
# ============================================================

def reviewer_agent_node(state: MultiAgentState):
    print("\n")
    print("=" * 70)
    print("AGENT")
    print("Reviewer Agent")
    print("=" * 70)
    draft = state.get("draft_answer", "")
    # ========================================================
    # Review Only 요청
    #
    # Draft가 없다면 User Question에 포함된
    # 설명을 검토 대상으로 사용
    # ========================================================
    review_target = draft if draft else state["question"]
    reviewer_messages = state.get("reviewer_messages", [])
    review_in_progress = state.get("review_in_progress", False)
    # ========================================================
    # CASE 1
    #
    # 새로운 Review Cycle 시작
    # ========================================================
    if not review_in_progress:
        human_message = (
            HumanMessage(
                content=(
                    f"""
검토할 내용:

{review_target}


Audience:

{state["audience"]}


Research Summary:

{state.get("research_summary", "")}


이 Draft에서 중요한 Agent 개념을 찾고 Reviewer Tool을 사용해 개념과 품질 기준을 검증하세요.
"""
                )
            )
        )
        response = (
            reviewer_model_with_tools.invoke(
                [
                    SystemMessage(
                        content=REVIEWER_TOOL_SYSTEM_PROMPT
                    ),
                    human_message
                ]
            )
        )
        print()
        print("[REVIEWER TOOL CALLS]")
        print(response.tool_calls)
        # ====================================================
        # Tool Call이 있으면 ToolNode로
        # ====================================================
        if response.tool_calls:
            return {
                'review_in_progress': True,
                'review_messages': [human_message, response],
                'execution_order': ['reviewer_agent']
            }

        # ====================================================
        # Tool Call이 없으면 바로 평가
        # ====================================================
        tool_evidence = []
    else:
        # ====================================================
        # CASE 2
        #
        # Tool 실행 후 다시 Reviewer로 돌아옴
        # ====================================================

        tool_messages = get_current_cycle_tool_messages(reviewer_messages)

        tool_evidence = [
            {
                'tool':message.name,
                'content': message.content
            }
            for message in tool_messages
        ]

    print()
    print("[REVIEW TOOL EVIDENCE]")
    print(
        json.dumps(
            tool_evidence,
            ensure_ascii=False,
            indent=2
        )
    )
    # ========================================================
    # 최종 Review 평가
    # ========================================================
    review_prompt = f"""
당신은 Reviewer Agent입니다.

다음 검토 대상과 Reviewer Tool Evidence를 이용해 최종 품질 평가를 수행하세요.


사용자의 원래 질문:

{state["question"]}


검토 대상:

{review_target}


Research Summary:

{state.get("research_summary", "")}


Reviewer Tool Evidence:

{
    json.dumps(
        tool_evidence,
        ensure_ascii=False,
        indent=2
    )
}


평가 기준:

1. 질문에 직접 답했는가?
2. Tool Reference와 개념적으로 일치하는가?
3. 중요한 오류가 없는가?
4. Audience에 적합한가?
5. 수정이 필요한 구체적인 지시를 작성했는가?


score는 0~100.

중요한 문제가 없고 score >= {MIN_REVIEW_SCORE}이면
passed=True로 평가하세요.
"""
    result = review_evaluator.invoke([HumanMessage(content=review_prompt)])
    passed = result.passed and result.score >= MIN_REVIEW_SCORE and (len(result.issues) == 0)
    print()
    print("[REVIEW RESULT]")
    print("Score:", result.score)
    print("Passed:", passed)
    print()
    print("Issues:")
    if result.issues:
        for issue in result.issues:
            print("-", issue)
    else:
        print("- 없음")
    # ========================================================
    # Review Only 결과
    # ========================================================
    if not draft:
        final_text = (
            "[검토 결과]\n"
            f"점수: {result.score}\n"
            f"통과 여부: {passed}\n\n"
            "[문제점]\n"
            +
            (
                "\n".join(
                    f"- {issue}"
                    for issue
                    in result.issues
                )
                if result.issues
                else "- 특별한 문제 없음"
            )
            +
            "\n\n[종합 의견]\n"
            +
            result.feedback
        )
    else:
        final_text = draft
    return {
        "review_done": True,
        "review_in_progress": False,
        "review_passed": passed,
        "review_score": result.score,
        "review_feedback": result.feedback,
        "review_issues": result.issues,
        "revision_instructions": result.revision_instructions,
        "final_answer": final_text,
        "execution_order": ["reviewer_agent"],
    }

# ============================================================
# 29. Reviewer Agent Router
# ============================================================

def route_after_reviewer_agent(state: MultiAgentState):

    messages = state.get('reviewer_messages', [])

    if messages:
        last_message = messages[-1]

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return 'reviewer_tools'

    if state.get('review_done', False):
        return 'supervisor'

    return 'supervisor'


# ============================================================
# 30. Reviewer Tool Audit
# ============================================================

def inspect_reviewer_tools_node(state: MultiAgentState):
    names = get_trailing_tool_names(
            state.get('reviewer_messages', [])
        )
    
    print('\n[REVIEWER TOOL AUDIT]')
    print(names)

    return {
        'tool_audit': [
            {
                'agent': 'reviewer_agent',
                'allowed_tools': [
                    tool_object.name
                    for tool_object in REVIEWER_TOOLS
                ],
                'executed_tools': names
            }
        ],
        'execution_order': ['reviewer_tools']
    }
    

# ============================================================
# 31. Supervisor Prompt
# ============================================================

SUPERVISOR_SYSTEM_PROMPT = """
당신은 Multi-Agent Supervisor입니다.

전문 Agent:

1. research_agent
2. writer_agent
3. reviewer_agent

============================================================
Research
============================================================

내부 자료 조사나 개념 분석이 필요한 경우 사용합니다.

Research Agent만 검색 Tool을 가지고 있습니다.


============================================================
Writer
============================================================

최종 설명문, 대본, 문장 작성 및 수정 담당입니다.

Writer Agent에는 Tool이 없습니다.



============================================================
Reviewer
============================================================

Draft 검증과 품질 평가를 담당합니다.

Reviewer는 검증 전용 Tool만 가지고 있습니다.


============================================================
Request Type
============================================================

research_ony:
조사만 필요

explain:
조사 후 사용자용 설명 필요

write:
문장 작성/대본/수정

review_only:
제공된 설명 검토만 필요

review_and_fix:
검토 후 문제가 있으면 수정 필요


============================================================
일반 흐름
============================================================

explain:
Research -> Writer -> Reviewer

research_only:
Research -> Finish

write:
Writer -> Reviewer

review_only:
Reviewer -> Finish

review_and_fix:
Reviewer -> Writer -> Reviewer


============================================================
중요
============================================================

Agent별 Tool 역할을 존중하세요.

Writer에게 검색을 맡기지 마세요.

Reviewer에게 새로운 자료 조사를 맡기지 마세요.

Research에게 Draft 품질 검토를 맡기지 마세요.
"""

# ============================================================
# 32. 최종 결과 선택
# ============================================================

def choose_final_answer(state: MultiAgentState):
    if state.get("draft_answer", ""):
        return state["draft_answer"]
    if state.get("final_answer", ""):
        return state["final_answer"]
    if state.get("research_summary", ""):
        return state["research_summary"]
    return "충분한 결과를 생성하지 못했습니다."

# ============================================================
# 33. Supervisor Helper
# ============================================================

def supervisor_goto(
    state: MultiAgentState,
    round_number: int,
    next_agent: str,
    reason: str,
    task: str = "",
    request_type: str | None = None,
):

    history = {
        'round':round_number,
        'next_agent': next_agent,
        'reason': reason
    }

    updates = {
        'supervisor_round': round_number,
        'delegated_task': task,
        'supervisor_reason': reason,
        'route_history': [history],
        'execution_order': ['supervisor']
    }

    if request_type is not None:
        updates['request_type'] = request_type

    if next_agent == 'finish':
        updates['final_answer'] = choose_final_answer(state)
        return Command(
            update=updates,
            goto=END
        )

    return Command(
        update=updates,
        goto=next_agent
    )


# ============================================================
# 34. Supervisor
# ============================================================

def supervisor_node(
    state: MultiAgentState,
) -> Command[
    Literal["research_agent", "writer_agent", "reviewer_agent", "__end__"]
]:
    print("\n")
    print("=" * 70)
    print("SUPERVISOR")
    print("=" * 70)
    current_round = state.get("supervisor_round", 0) + 1
    request_type = state.get("request_type", "")
    research_done = state.get("research_done", False)
    writer_done = state.get("writer_done", False)
    review_done = state.get("review_done", False)
    review_passed = state.get("review_passed", False)
    # ========================================================
    # 최대 Loop
    # ========================================================
    
    if current_round > MAX_SUPERVISOR_ROUNDS:
        return supervisor_goto(
            state,
            current_round,
            'finish',
            'Supervisor 최대 반복 횟수 도달'
        )

    # ========================================================
    # Reviewer PASS
    # ========================================================

    if review_passed:
        return supervisor_goto(
            state,
            current_round,
            'finish',
            'Reviewer가 결과를 통과시켰습니다.'
        )

    # ========================================================
    # Research Only
    # ========================================================

    if request_type == 'research_only' and research_done:
        return supervisor_goto(
            state,
            current_round,
            'finish',
            '사용자가 Research 결과만 요청했습니다.'
        )

    # ========================================================
    # Review Only
    # ========================================================

    if request_type == 'review_only' and review_done:
        return supervisor_goto(
            state,
            current_round,
            'finish',
            'Review Only 요청이 완료되었습니다.'
        )

    # ========================================================
    # Explain:
    #
    # Research 완료
    # ↓
    # Writer
    # ========================================================

    if request_type == 'explain' and research_done and (not writer_done):
        return supervisor_goto(
            state,
            current_round,
            'writer_agent',
            'Research Evidence가 준비되었습니다.',
            'Research 결과만 사용하여 사용자용 설명을 작성하세요.'
        )


    # ========================================================
    # Writer 완료
    # ↓
    # Reviewer
    # ========================================================

    if writer_done and (not review_done):
        return supervisor_goto(
            state,
            current_round,
            'reviewer_agent',
            '새 Draft가 생성되어 검토가 필요합니다.',
            'Draft의 Agent 개념과 Audience 적합성을 검증하세요.'
        )


    # ========================================================
    # Reviewer FAIL + Draft 있음
    # ↓
    # Writer Revision
    # ========================================================
    
    if review_done and (not review_passed) and state.get('draft_answer', ''):
        if state.get('revision_count') >= MAX_WRITER_REVISIONS:
            return supervisor_goto(
                state,
                current_round,
                'finish',
                '최대 Writer Revision 횟수에 도달했습니다.'
            )

        return supervisor_goto(
            state,
            current_round,
            'writer_agent',
            'Reviewer가 Draft의 문제를 발견했습니다.',
            'Reviewer Feedback과 Revision Instructions를 반영하여 Draft를 수정하세요.'
        )


    # ========================================================
    # Review and Fix:
    #
    # Review Only로 먼저 검토했는데
    # 문제가 발견되고 Draft가 아직 없는 경우
    # ↓
    # Writer
    # ========================================================

    if (
        request_type == 'review_and_fix'
        and
        review_done
        and
        not review_passed
        and
        not state.get('draft_answer', '')
    ):
        return supervisor_goto(
            state,
            current_round,
            'writer_agent',
            '사용자 제공 설명에서 문제가 발견되었습니다.',
            'Reviewer의 검토를 바탕으로 올바른 설명을 작성하세요.'
        )


    # ========================================================
    # 최초 Supervisor 판단
    # ========================================================
    summary = {
        "question":
            state["question"],
        "audience":
            state["audience"],
        "research_done": research_done,
        "writer_done": writer_done,
        "review_done": review_done,
    }
    decision = (
        supervisor_model.invoke(
            [
                SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"""
현재 요청:

{
    json.dumps(
        summary,
        ensure_ascii=False,
        indent=2
    )
}

Request Type과 첫 번째 Agent를 결정하세요.
"""
                    )
                ),
            ]
        )
    )

    print('\n[SUPERVISOR DECISION]')
    print(f'Request Type: {decision.request_type}')
    print(f'Next Agent: {decision.next_agent}')
    print(f'Reason: {decision.reason}')


    return supervisor_goto(
        state,
        current_round,
        decision.next_agent,
        decision.reason,
        decision.task_for_agent,
        decision.request_type
    )





# ============================================================
# 35. Research ToolNode
# ============================================================
#
# Research ToolNode에는:
#
# RESEARCH_TOOLS만 등록
#
#
# messages_key:
#
# research_messages
#
# ============================================================

research_tool_node = ToolNode(
    RESEARCH_TOOLS,
    messages_key='research_messages',
    handle_tool_errors=True
)


# ============================================================
# 36. Reviewer ToolNode
# ============================================================
#
# Reviewer ToolNode에는:
#
# REVIEWER_TOOLS만 등록
#
#
# messages_key:
#
# reviewer_messages
#
# ============================================================

reviewer_tool_node = ToolNode(
    REVIEWER_TOOLS,
    messages_key='reviewer_messages',
    handle_tool_errors=True
)

# ============================================================
# 37. Graph
# ============================================================

builder = StateGraph(MultiAgentState)

# ============================================================
# Supervisor
# ============================================================

builder.add_node("supervisor", supervisor_node)

# ============================================================
# Research
# ============================================================

builder.add_node('research_agent', research_agent_node)
builder.add_node('research_tools', research_tool_node)
builder.add_node('inspect_research_tools', inspect_research_tools_node)

# ============================================================
# Writer
# ============================================================

builder.add_node("writer_agent", writer_agent_node)

# ============================================================
# Reviewer
# ============================================================

builder.add_node('reviewer_agent', reviewer_agent_node)
builder.add_node('reviewer_tools', reviewer_tool_node)
builder.add_node('inspect_reviewer_tools', inspect_reviewer_tools_node)

# ============================================================
# START
# ↓
# Supervisor
# ============================================================

builder.add_edge(START, "supervisor")


# ============================================================
# Research Agent
#
# Tool Call?
#
# YES
# ↓
# Research ToolNode
#
# NO / 완료
# ↓
# Supervisor
# ============================================================

builder.add_conditional_edges(
    'research_agent',
    route_after_research_agent,
    {
        'research_tools': 'research_tools',
        'supervisor': 'supervisor'
    }
)


# ============================================================
# Research Tool
# ↓
# Audit
# ↓
# Research Agent
# ============================================================

builder.add_edge('research_tools', 'inspect_research_tools')
builder.add_edge('inspect_research_tools', 'research_agent')

# ============================================================
# Writer
# ↓
# Supervisor
#
# Writer는 Tool Node가 없다.
# ============================================================

builder.add_edge("writer_agent", "supervisor")

# ============================================================
# Reviewer Agent
#
# Tool Call?
#
# YES
# ↓
# Reviewer ToolNode
#
# 완료
# ↓
# Supervisor
# ============================================================

builder.add_conditional_edges(
    'reviewer_agent',
    route_after_reviewer_agent,
    {
        'reviewer_tools': 'reviewer_tools',
        'supervisor': 'supervisor'
    }
)

# ============================================================
# Reviewer Tool
# ↓
# Audit
# ↓
# Reviewer
# ============================================================

builder.add_edge('reviewer_tools', 'inspect_reviewer_tools')
builder.add_edge('inspect_reviewer_tools', 'reviewer_agent')

# ============================================================
# Compile
# ============================================================

multi_agent_graph = builder.compile()

# ============================================================
# 38. Tool Audit 출력
# ============================================================

def print_tool_audit(audit_items):
    print("\n")
    print("=" * 70)
    print("TOOL PERMISSION AUDIT")
    print("=" * 70)
    if not audit_items:
        print("Tool 실행 기록 없음")
        return
    for item in audit_items:
        print()
        print("Agent:", item.get("agent"))
        print("Allowed:")
        allowed = item.get("allowed_tools", [])
        if allowed:
            for tool_name in allowed:
                print(" -", tool_name)
        else:
            print(" - 없음")
        print("Executed:")
        executed = item.get("executed_tools", [])
        if executed:
            for tool_name in executed:
                print(" -", tool_name)
        else:
            print(" - 없음")

# ============================================================
# 39. 실행 함수
# ============================================================

def run_multi_agent(question: str, audience: str, expected_flow: str, expected_tool_behavior: str):
    print("\n\n")
    print("#" * 70)
    print("MULTI-AGENT 4")
    print("AGENT-SPECIFIC TOOLS")
    print("#" * 70)
    print()
    print("[QUESTION]")
    print(question)
    print()
    print("[EXPECTED FLOW]")
    print(expected_flow)
    print()
    print("[EXPECTED TOOL BEHAVIOR]")
    print(expected_tool_behavior)
    initial_state = {
        "question": question,
        "audience": audience,
        # Supervisor
        "request_type": "",
        "supervisor_round": 0,
        "delegated_task": "",
        "supervisor_reason": "",
        # Research
        "research_done": False,
        "research_summary": "",
        "research_evidence": [],
        "research_messages": [],
        # Writer
        "writer_done": False,
        "draft_answer": "",
        "revision_count": 0,
        # Reviewer
        "review_done": False,
        "review_in_progress": False,
        "review_passed": False,
        "review_score": 0,
        "review_feedback": "",
        "review_issues": [],
        "revision_instructions": [],
        "reviewer_messages": [],
        # Trace
        "execution_order": [],
        "route_history": [],
        "tool_audit": [],
        # Final
        "final_answer": "",
    }
    result = multi_agent_graph.invoke(initial_state, config={"recursion_limit": 35})
    # ========================================================
    # Summary
    # ========================================================
    print("\n")
    print("#" * 70)
    print("EXECUTION SUMMARY")
    print("#" * 70)
    print()
    print("Execution Order:")
    print(" → ".join(result.get("execution_order", [])))
    print()
    print("Request Type:", result.get("request_type", ""))
    print("Supervisor Rounds:", result.get("supervisor_round", 0))
    print("Research Done:", result.get("research_done", False))
    print("Writer Done:", result.get("writer_done", False))
    print("Review Done:", result.get("review_done", False))
    print("Review Passed:", result.get("review_passed", False))
    print("Review Score:", result.get("review_score", 0))
    # ========================================================
    # Route
    # ========================================================
    print("\n")
    print("=" * 70)
    print("SUPERVISOR ROUTE HISTORY")
    print("=" * 70)
    for route in result.get("route_history", []):
        print()
        print("Round:", route.get("round"))
        print("Next:", route.get("next_agent"))
        print("Reason:", route.get("reason"))
    # ========================================================
    # Tool Audit
    # ========================================================
    print_tool_audit(result.get("tool_audit", []))
    # ========================================================
    # Final
    # ========================================================
    print("\n")
    print("=" * 70)
    print("FINAL ANSWER")
    print("=" * 70)
    print()
    print(result.get("final_answer", ""))
    return result

# ============================================================
# 40. 다양한 테스트 질문
# ============================================================

TEST_CASES = [
    # ========================================================
    # EXAMPLE 1
    #
    # Research Tool
    # ↓
    # Writer Tool 없음
    # ↓
    # Reviewer Tool
    # ========================================================
    {
        "name": "Tool Permission Explanation",
        "question": (
            "Multi-Agent에서 Agent마다 서로 다른 Tool을 "
            "주어야 하는 이유를 학생들에게 예를 들어 설명해줘."
        ),
        "audience": "instructor",
        "expected_flow": (
            "Supervisor → Research Agent → Research Tools "
            "→ Research Agent → Supervisor → Writer "
            "→ Supervisor → Reviewer → Reviewer Tools "
            "→ Reviewer → Supervisor → Finish"
        ),
        "expected_tool": (
            "Research는 내부 검색/예제 Tool 사용, "
            "Writer는 Tool 없음, "
            "Reviewer는 Reference/Checklist Tool 사용"
        ),
    },
    # ========================================================
    # EXAMPLE 2
    #
    # Research Only
    # ========================================================
    {
        "name": "Research Only",
        "question": (
            "Agent별 Tool Permission을 설계할 때 "
            "고려해야 할 포인트만 조사해줘. "
            "최종 강의문은 작성하지 마."
        ),
        "audience": "instructor",
        "expected_flow": (
            "Supervisor → Research → Research Tools "
            "→ Research → Supervisor → Finish"
        ),
        "expected_tool": (
            "Research Tool만 사용. "
            "Writer/Reviewer Tool 사용 없음"
        ),
    },
    # ========================================================
    # EXAMPLE 3
    #
    # Writer Direct
    #
    # Tool 0개
    # ========================================================
    {
        "name": "Writer No Tool",
        "question": (
            "다음 문장을 자연스러운 수업 도입 멘트로 "
            "다듬어줘.\n\n"
            "'에이전트마다 사용할 수 있는 도구가 다릅니다.'"
        ),
        "audience": "instructor",
        "expected_flow": (
            "Supervisor → Writer → Supervisor "
            "→ Reviewer → Reviewer Tools → Reviewer "
            "→ Supervisor → Finish"
        ),
        "expected_tool": (
            "Writer는 Tool을 하나도 사용하지 않아야 함. "
            "Reviewer만 검증 Tool 사용 가능"
        ),
    },
    # ========================================================
    # EXAMPLE 4
    #
    # Reviewer Only
    # ========================================================
    {
        "name": "Review Only",
        "question": (
            "다음 설명이 맞는지 검토만 해줘.\n\n"
            "'Writer Agent가 최종 문장을 작성할 때는 "
            "항상 Research Agent와 동일한 검색 Tool을 "
            "가지고 있어야 한다.'"
        ),
        "audience": "intermediate",
        "expected_flow": (
            "Supervisor → Reviewer → Reviewer Tools "
            "→ Reviewer → Supervisor → Finish"
        ),
        "expected_tool": (
            "Research Tool 없이 Reviewer 검증 Tool만 사용"
        ),
    },
    # ========================================================
    # EXAMPLE 5
    #
    # Router / Handoff / Supervisor
    # 여러 Reference Tool 가능
    # ========================================================
    {
        "name": "Architecture Comparison",
        "question": (
            "Router, Handoff, Supervisor의 차이를 "
            "Agent 실행 흐름 예제와 함께 설명해줘."
        ),
        "audience": "intermediate",
        "expected_flow": (
            "Research → Writer → Reviewer"
        ),
        "expected_tool": (
            "Research가 관련 문서를 검색하고, "
            "Reviewer가 router/handoff/supervisor "
            "Reference를 여러 개 검증할 수 있음"
        ),
    },
    # ========================================================
    # EXAMPLE 6
    #
    # Context Isolation + Tool Permission
    # ========================================================
    {
        "name": "Context and Tool Isolation",
        "question": (
            "Context Isolation과 Tool Permission Isolation은 "
            "무엇이 다르고 왜 둘 다 필요한지 설명해줘."
        ),
        "audience": "instructor",
        "expected_flow": (
            "Research → Writer → Reviewer"
        ),
        "expected_tool": (
            "Research 검색 Tool과 Reviewer 검증 Tool이 "
            "서로 분리되어 실행"
        ),
    },
    # ========================================================
    # EXAMPLE 7
    #
    # 잘못된 설명 검토 + 수정
    # ========================================================
    {
        "name": "Review and Fix",
        "question": (
            "다음 설명을 검토하고 틀렸다면 고쳐줘.\n\n"
            "'Tool Permission Isolation은 모든 Agent에게 "
            "모든 Tool을 제공한 뒤 Prompt로 사용하지 말라고 "
            "지시하는 방식이다.'"
        ),
        "audience": "intermediate",
        "expected_flow": (
            "Reviewer → Reviewer Tools → Supervisor "
            "→ Writer → Supervisor → Reviewer "
            "→ Reviewer Tools → Supervisor → Finish"
        ),
        "expected_tool": (
            "Reviewer는 verify Tool 사용, "
            "Writer는 수정 과정에서도 Tool 없음"
        ),
    },
    # ========================================================
    # EXAMPLE 8
    #
    # Reflection과 Tool Permission
    # ========================================================
    {
        "name": "Reflection Tool Separation",
        "question": (
            "Reflection Agent에서 생성 Agent와 "
            "검토 Agent에게 같은 Tool을 주지 않아도 되는 "
            "이유를 설명해줘."
        ),
        "audience": "intermediate",
        "expected_flow": (
            "Research → Writer → Reviewer"
        ),
        "expected_tool": (
            "조사와 검증 Tool 역할이 분리됨"
        ),
    },
    # ========================================================
    # EXAMPLE 9
    #
    # 최소 권한 개념
    # ========================================================
    {
        "name": "Least Tool Permission",
        "question": (
            "Agent에게 필요한 Tool만 주는 최소 권한 방식이 "
            "Multi-Agent 설계에서 어떤 장점이 있는지 "
            "핵심 포인트만 조사해줘."
        ),
        "audience": "instructor",
        "expected_flow": (
            "Research → Research Tools → Finish"
        ),
        "expected_tool": (
            "Research Tool만 사용"
        ),
    },
    # ========================================================
    # EXAMPLE 10
    #
    # ToolNode
    # ========================================================
    {
        "name": "ToolNode Role",
        "question": (
            "Agent별 Tool Permission과 ToolNode가 "
            "어떤 관계인지 초보자도 이해할 수 있게 설명해줘."
        ),
        "audience": "beginner",
        "expected_flow": (
            "Research → Writer → Reviewer"
        ),
        "expected_tool": (
            "Research는 ToolNode 자료 조사, "
            "Reviewer는 ToolNode Reference 검증"
        ),
    },
    # ========================================================
    # EXAMPLE 11
    #
    # Parallel Tool
    # ========================================================
    {
        "name": "Reviewer Multiple Tools",
        "question": (
            "Router, Handoff, Supervisor를 비교하면서 "
            "각 개념이 정확한지도 검증한 설명을 만들어줘."
        ),
        "audience": "instructor",
        "expected_flow": (
            "Research → Writer → Reviewer"
        ),
        "expected_tool": (
            "Reviewer가 여러 verify_concept_reference "
            "Tool Call을 생성할 수 있음"
        ),
    },
    # ========================================================
    # EXAMPLE 12
    #
    # 전체 구조
    # ========================================================
    {
        "name": "Full Multi-Agent Architecture",
        "question": (
            "Supervisor, Shared State, Context Isolation, "
            "Agent별 Tool Permission을 하나의 Multi-Agent "
            "구조로 연결해서 수업용으로 설명해줘."
        ),
        "audience": "instructor",
        "expected_flow": (
            "Research → Writer → Reviewer"
        ),
        "expected_tool": (
            "Agent별로 서로 다른 Tool Permission을 "
            "실제 실행 로그에서 확인"
        ),
    },
]

# ============================================================
# 41. 실행 설정
# ============================================================

RUN_ALL_EXAMPLES = True

# ============================================================
# Example
#
# 0  Tool Permission 종합
# 1  Research Only
# 2  Writer No Tool
# 3  Reviewer Only
# 4  Router/Handoff/Supervisor
# 5  Context + Tool Isolation
# 6  Review and Fix
# 7  Reflection
# 8  최소 권한
# 9  ToolNode
# 10 Reviewer Multi Tool
# 11 전체 Architecture
#
# ============================================================

DEFAULT_EXAMPLE_INDEX = 0

# ============================================================
# 42. Main
# ============================================================

if __name__ == "__main__":
    # ========================================================
    # Agent별 Tool Permission 먼저 확인
    # ========================================================
    print_tool_permissions()
    # ========================================================
    # 모든 예제
    # ========================================================
    if RUN_ALL_EXAMPLES:
        for (index, test) in enumerate(TEST_CASES, start=1):
            print("\n\n")
            print("#" * 70)
            print(
                f"EXAMPLE {index}"
            )
            print(test["name"])
            print("#" * 70)
            run_multi_agent(
                question=test["question"],
                audience=test["audience"],
                expected_flow=test["expected_flow"],
                expected_tool_behavior=test["expected_tool"],
            )
    # ========================================================
    # 하나만 실행
    # ========================================================
    else:
        test = TEST_CASES[DEFAULT_EXAMPLE_INDEX]
        print()
        print("실행 예제:", test["name"])
        run_multi_agent(
            question=test["question"],
            audience=test["audience"],
            expected_flow=test["expected_flow"],
            expected_tool_behavior=test["expected_tool"],
        )