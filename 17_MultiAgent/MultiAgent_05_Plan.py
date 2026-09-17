# ============================================================
# ============================================================
'''
planer -> dynamic workers -> synthesizer

1. planer가 subtask 직접 생성
2. subtask 개수 Runtime에 결정
3. send api로 worker 동적 생성
4. worker마다 서로 다른 custom state
5. worker들은 병렬 실행
6. reducer로 worker 결과 누적
7. synthesizer로 최종 통합
'''
# ============================================================
# 1. Import
# ============================================================

import json
import os
import time
from operator import add
from typing import Annotated, Literal, TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Send

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
# 4. Planner Structured Output
# ============================================================

SubtaskType = Literal[
    'concept',
    'comparison',
    'implementation',
    'example',
    'risk',
    'review'
]


# ============================================================
# 하나의 Subtask
# ============================================================

class SubTask(BaseModel):

    # 최종 결과에서 사용할 논리적 순서
    # 병렬 Worker 완료 순서와 다를 수 있기 때문에 명시적으로 order를 둔다.
    order: int = Field(
        ge=1,
        description='최종 결과에서 사용할 논리적 순서. 1부터 시작'
    )

    # Subtask 제목
    title: str = Field(
        description='Subtask의 짧고 명확한 제목'
    )

    # 작업 유형
    task_type: SubtaskType = Field(
        description='Subtask의 성격'
    )

    # Worker에게 실제 전달할 작업
    instruction: str = Field(
        description='다른 Worker 결과 없이도 독립적으로 수행할 수 있는 구체적인 작업 지시'
    )

    # 기대 효과
    expected_output: str = Field(
        description='Worker가 반환해야 할 결과의 핵심 형태'
    )


# ============================================================
# 전체 Planner 결과
# ============================================================

class TaskPlan(BaseModel):

    plan_reason: str = Field(
        description='왜 이 Subtask 구성으로 분해했는지 설명'
    )

    subtasks: list[SubTask] = Field(
        min_length=1,
        max_length=6,
        description=(
            '병렬 실행 가능한 독립 Subtask 목록. '
            '사용자가 개수나 영역을 명시하면 가능한 그대로 따른다.'
        )
    )


# ============================================================
# Planner Model
# ============================================================

planner_model = base_model.with_structured_output(TaskPlan)

# ============================================================
# 5. Overall State
#
# Annotated[list[dict], add]
# ============================================================


class OverallState(TypedDict):

    # User Input
    question: str
    audience: str

    # Planner
    plan_reason: str
    subtasks: list[dict]

    # Parallel Worker Output => Reducer
    completed_tasks: Annotated[list[dict], add]

    # Worker 실행 기록 => 여러 Worker가 동시에 업데이트한다.
    worker_execution_log: Annotated[list[dict], add]

    # final
    final_answer: str


# ============================================================
# 6. Worker Input State
# 
# Worker는 OverallState 전체를 받지 않는다.
# Send에서 필요한 정보만 따로 전달한다.
# ============================================================


class WorkerState(TypedDict):
    question: str
    audience: str
    task_order: int
    task_title: str
    task_type: SubtaskType
    task_instruction: str
    expected_output: str



# ============================================================
# 7. Planner Prompt
# ============================================================

PLANNER_SYSTEM_PROMPT = """
당신은 Multi-Agent 시스템의 Planner입니다.

당신의 역할은 사용자의 복잡한 요청을 여러 개의 독립적인 Subtask로 분해하는 것입니다.

중요한 목표는 Subtask들을 LangGraph Send API로 동시에 실행할 수 있게 만드는 것입니다.



============================================================
핵심 원칙
============================================================

1. 각 Subtask는 다른 Subtask의 결과를 기다리지 않고 독립적으로 
수행할 수 있어야 합니다.


2. 서로 결과 의존성이 있는 작업은 별도 Subtask로 분리하지 마세요.

나쁜 예:

Subtask 1:

RAG를 조사한다.


Subtask 2:

Subtask 1의 조사 결과를 읽고 강의문을 작성한다.


Subtask 2는 Subtask 1에 의존하므로 병렬 Worker로 적합하지 않습니다.


좋은 예:

Subtask 1:

RAG의 핵심 구조를 독립적으로 분석한다.


Subtask 2:

RAG를 설명할 교육용 비유를 독립적으로 만든다.


Subtask 3:

RAG 설계 시 주의점을 독립적으로 분석한다.



3. 사용자가 명시적으로 영역을 나열했다면 각 영역을 별도 Subtask로 만드는 것을 우선합니다.


예:

"Tool Calling, RAG, Memory, Reflection, Multi-Agent 다섯 영역을 각각 평가해줘."

-> 5개의 Subtask



4. 사용자가:
"하나의 통합 작업으로" 라고 명시하면 Subtask 1개로 제한합니다.



5. 필요 이상으로 작업을 잘게 쪼개지 마세요.



6. 최대 6개 Subtask까지만 생성하세요.



============================================================
Task Type
============================================================

concept:
핵심 개념, 정의, 원리 분석

comparison:
두 개 이상의 개념 비교

implementation:
코드, Workflow, 설계 구조 분석

example:
교육용 예제, 비유, 시나리오

risk:
주의점, 한계, 실패 가능성, 비용 문제

review:
특정 영역의 완성도나 학습 상태 평가



============================================================
order
============================================================

병렬 실행 완료 순서는 보장되지 않습니다.

따라서 order는 최종 Synthesizer가 결과를 다시 정렬할 때 사용할
논리적 순서입니다.

1부터 연속되게 작성하세요.



============================================================
중요
============================================================

Planner는 사용자 최종 답변을 작성하지 않습니다.

오직:

- 어떤 Subtask가 필요한가?
- 각 Worker가 무엇을 독립적으로 해야 하는가?

를 설계합니다.
"""



# ============================================================
# 8. Planner Node
# ============================================================

def planner_node(state: OverallState):
    print('\n')
    print('='*80)
    print('[planner_node 실행]')
    print('='*80)
    print('\n[question]')
    print(state['question'])

    start_time = time.perf_counter()
    # ============================================================
    # Planner 실행
    # ============================================================

    plan = planner_model.invoke(
        [
            SystemMessage(
                content=PLANNER_SYSTEM_PROMPT
            ),
            HumanMessage(
                content=f"""
사용자 질문:

{state["question"]}


Audience:

{state["audience"]}


병렬 실행 가능한 독립적 Subtask 계획을 작성하세요.
"""
            )
        ]
    )

    elapsed = time.perf_counter() - start_time

    # ============================================================
    # 중복 Subtask 제거
    # ============================================================

    seen = set()
    subtasks = []

    for index, task in enumerate(plan.subtasks, start=1):
        key = (task.title.strip().lower(), task.instruction.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        '''
        Planner가 order를 이상하게 주더라도 코드에서 => 1, 2, 3.... 정리해줘야함
        '''
        subtasks.append(
            {
                'order': index,
                'title': task.title,
                'task_type': task.task_type,
                'instruction': task.instruction,
                'expected_output': task.expected_output
            }            
        )

    # ============================================================
    # Safety Fallback
    # ============================================================
    if not subtasks:
        subtasks = [
            {
                'order': 1,
                'title': '핵심 요청 분석',
                'task_type': 'concept',
                'instruction':(
                    '사용자 질문의 핵심 내용을 독립적으로 분석한다.'
                ),
                'expected_output': '핵심 개념과 설명'
            }
        ]

    print('\n[Plan Reason]')
    print(plan.plan_reason)
    print('\n[Subtasks]')

    for task in subtasks:
        print(f'\n{task["order"]}. {task["title"]}')
        print(f'    type: {task["task_type"]}')
        print(f'    instruction: {task["instruction"]}')
        print(f'    expected: {task["expected_output"]}')

    print(f'\nPlanner Duration: {round(elapsed, 3)} sec')
    print(f'plan_reason: {plan.plan_reason}, subtasks: {subtasks}')

    return {
        'plan_reason': plan.plan_reason,
        'subtasks': subtasks
    }


# ============================================================
# 9. Send Dispatcher
# ============================================================

def assign_workers(state: OverallState):
    print('\n')
    print('='*80)
    print('Send Dispatch')
    print('='*80)

    sends = []

    for task in state['subtasks']:
        print(f'Send -> worker | der={task["order"]} | title={task["title"]}')

        sends.append(
            Send(
                'worker',
                {
                    'question': state['question'],
                    'audience': state['audience'],
                    'task_order': task['order'],
                    'task_title': task['title'],
                    'task_type': task['task_type'],
                    'task_instruction': task['instruction'],
                    'expected_output': task['expected_output']
                }
            )
        )

    return sends



# ============================================================
# 10. Worker System Prompt 생성
# ============================================================


def build_worker_system_prompt(task_type: str) -> str:

    common = """
당신은 Planner가 생성한 하나의 Subtask만 담당하는 전문 Worker입니다.

다른 Worker의 결과를 볼 수 없으면, 볼 필요도 없습니다.

현재 할당된 작업만 독립적으로 완성하세요.

사용자의 전체 질문을 참고하되 다른 Subtask까지 대신 처리하지 마세요.

결과는 나중에 Synthesizer가 다른 Worker 결과와 합칩니다.

사실을 임의로 만들어내지 마세요.
"""

    specialized = {
        'concept': '핵심 정의, 목적, 원리와 중요한 개념 관계를 정확하게 설명하세요',
        'comparison': '비교 기준을 명확하게 세우고 공통점과 차이점을 구조적으로 정리하세요',
        'implementation': (
            'State, Node, Edge, Tool, Workflow, 데이터 흐름 등 '
            '구현 구조를 단계적으로 분석하세요.'
        ),
        'example': '학생이 이해하기 쉬운 비유, 실제 질문, 실행 시나리오 또는 간단한 코드 흐름을 제시하세요.',
        'risk': '문제만 나열하지 말고 원인, 영향, 완화 방법까지 함께 분석하세요.',
        'review': '평가 기준을 먼저 세우고 강점, 부족한 점, 개선 방향을 구분해서 평가하세요.'
    }

    return common + specialized.get(task_type, '')


def get_response_text(response) -> str:
    text = getattr(response, 'text', None)
    if isinstance(text, str) and text:
        return text

    if isinstance(response.content, str):
        return response.content

    return str(response.content)


# ============================================================
# 11. Dynamic Worker Node
# ============================================================
# Graph에는 Worker Node가 하나뿐임
# 하지만 Send가 여러개 생성되면:
# Worker #1, Worker #2.....
# 처음 여러 독립 Worker Instance가 실행됨

def worker_node(state: WorkerState):

    print('\n')
    print('='*80)
    print('Dynamic Worker')
    print('='*80)
    print(f'order: {state["task_order"]}')
    print(f'title: {state["task_title"]}')
    print(f'type: {state["task_type"]}')


    # Send가 전달한 State 확인
    print('\n[Visible State Keys]')
    print(sorted(state.keys()))
    print('\n[Task]')
    print(state['task_instruction'])

    # Worker 실행
    start_time = time.perf_counter()

    response = base_model.invoke(
        [
            SystemMessage(
                content=build_worker_system_prompt(
                    state['task_type']
                )
            ),
            HumanMessage(
                content=f"""
사용자의 전체 질문:

{state["question"]}


Audience:

{state["audience"]}


당신의 Subtask 제목:

{state["task_title"]}


Subtask 지시:

{state["task_instruction"]}


기대 출력:

{state["expected_output"]}


이 Subtask만 독립적으로 수행하세요.
"""
            )
        ]
    )
    elapsed = time.perf_counter() - start_time
    result_text = get_response_text(response)

    print(f'\nWorker Duration: {round(elapsed, 3)} sec')

    result_item = {
        'order': state['task_order'],
        'title': state['task_title'],
        'task_type': state['task_type'],
        'instruction': state['task_instruction'],
        'result': result_text,
        'duration_seconds': round(elapsed, 3)
    }


    # debug log
    log_item = {
        'order': state['task_order'],
        'title': state['task_title'],
        'task_type': state['task_type'],
        'duration_seconds': round(elapsed, 3)
    }


    return {
        'completed_tasks': [result_item],
        'worker_execution_log': [log_item]
    }


# ============================================================
# 12. Synthesizer Prompt
# ============================================================

SYNTHESIZER_SYSTEM_PROMPT = """
당신은 Planner-Worker Multi-Agent 시스템의 Synthesizer입니다.

Planner가 사용자 요청을 여러 독립 Subtask로 분해했고, 각 Worker가 
자신의 Subtask 결과를 독립적으로 작성했습니다.

당신의 역할은 Worker 결과를 하나의 자연스럽고 일관된 최종 답변으로
통합하는 것입니다.



============================================================
통합 원칙
============================================================

1. 사용자의 원래 질문에 직접 답하세요.
2. Worker 결과를 단순히 그대로 이어 붙이지 마세요.
3. 중복된 설명은 합치세요.
4. 서로 다른 관점은 자연스럽게 연결하세요
5. Worker 결과 사이에 표현 차이가 있다면 핵심 의미를 비교해 정리하세요.
6. Worker가 제공하지 않은 구체적인 사실을 임으로 추가하지 마세요.
7. Planner의 논리적 order를 존중하되 읽기 좋은 최종 구조로 재구성할 수 있습니다.
8. Audience 수준에 맞게 설명하세요.


============================================================
중요
============================================================

병렬 Worker의 실제 완료 순서가 Planner의 논리적인 순서와 다를 수 있습니다.

입력 결과의 order를 기준으로 의미를 파악하세요.
"""

def synthesizer_node(state: OverallState):
    print('\n')
    print('='*80)
    print('Synthesizer')
    print('='*80)

    raw_results = state.get('completed_tasks')

    ordered_results = sorted(
        raw_results,
        key=lambda item: item['order']
    )

    print('\n[Raw Reducer Order]')
    print([
        item['title']
        for item in raw_results
    ])

    print('\n[Logical Order]')
    print(
        item['title']
        for item in ordered_results
    )


    synthesis_package = [
        {
            'order': item['order'],
            'title': item['title'],
            'task_type': item['task_type'],
            'result': item['result']
        }
        for item in ordered_results
    ]

    # 통합
    start_time = time.perf_counter()

    response = base_model.invoke(
        [
            SystemMessage(
                content=SYNTHESIZER_SYSTEM_PROMPT
            ),
            HumanMessage(
                content=f"""
사용자의 원래 질문:

{state["question"]}


Audience:

{state["audience"]}


Planner Reason:

{state["plan_reason"]}


Worker Results:

{
    json.dumps(
        synthesis_package,
        ensure_ascii=False,
        indent=2
    )
}


위 Worker 결과를 통합해 최종 답변을 작성하세요.
"""
            )
        ]
    )

    elapsed = time.perf_counter() - start_time
    final_answer = get_response_text(response)

    print('\n[Synthesized Answer]')
    print(final_answer)
    print(f'\n[Synthesizer Duration]: {round(elapsed, 3)} sec')

    return {
        'final_answer': final_answer
    }



builder = StateGraph(OverallState)


builder.add_node('planner', planner_node)

builder.add_node('worker', worker_node)

builder.add_node('synthesizer', synthesizer_node)




builder.add_edge(START, 'planner')


'''
planner -> Send()

assign worker가:

[
    Send('worker', state1),
    Send('worker', state2),
    ....
]
반환해줌
'''
builder.add_conditional_edges('planner', assign_workers, ['worker'])

builder.add_edge('worker', 'synthesizer')

builder.add_edge('synthesizer', END)


planner_worker_graph = builder.compile()


# ============================================================
# 13. Planner 결과 출력
# ============================================================

def print_plan(subtasks: list[dict]):
    print('\n')
    print('='*80)
    print('Final Planner Task List')
    print('='*80)

    for task in subtasks:
        print(f'\n{task["order"]}. {task["title"]}')
        print(f'type: {task["task_type"]}')
        print(f'instruction: {task["instruction"]}')



# ============================================================
# 14. Worker 결과 출력
# ============================================================

def print_worker_results(results: list[dict]):
    print('\n')
    print('='*80)
    print('Worker Result Details')
    print('='*80)

    ordered = sorted(
        results,
        key=lambda item: item['order']
    )

    for item in ordered:
        print('\n' + '=' * 80)
        print(f'Order: {item["order"]}')
        print(f'Title: {item["title"]}')
        print(f'Type: {item["task_type"]}')
        print(f'Duration: {item["duration_seconds"]} sec')
        print('\nResult:')
        print(item['result'])



# ============================================================
# 15. 실행 함수
# ============================================================
    
def run_planner_workers(
        question: str,
        audience: str,
        expected_subtask_count: int,
        expected_focus: str
):

    print('\n\n')
    print('#'*80)
    print('Multi Agent5')
    print('Planner -> Dynamic Workers -> Synthesizer')
    print('#'*80)

    print('\n[Question]')
    print(question)

    print(f'\n[Expected Subtask Count]: {expected_subtask_count}')
    print(f'\n[Expected Focus]')
    print(expected_focus)


    graph_start = time.perf_counter()

    result = planner_worker_graph.invoke(
        {
            'question': question,
            'audience': audience,
            'plan_reason': '',
            'subtasks': [],
            'completed_tasks': [],
            'worker_execution_log': [],
            'final_answer': ''
        },
        config={
            'recursion_limit': 20
        }
    )

    total_elapsed = time.perf_counter() - graph_start
    actual_count = len(result.get('completed_tasks', []))


    print('\n')
    print('#'*80)
    print('Execution Summary')
    print('#'*80)

    print('\nPlan Reason:')
    print(result.get('plan_reason', ''))

    print('\nExpected Subtask Count:')
    print(expected_subtask_count)

    print('\nActual Subtask Count:')
    print(actual_count)

    print('\nCount Match')
    print(actual_count == expected_subtask_count)

    # 병렬 완료 순서
    print('\nRaw Worker Completion Log:')
    print([
        item.get('title')
        for item in result.get('worker_execution_log', [])
    ])

    print(f'\nTotal Graph Duration: {round(total_elapsed, 3)} sec')

    print_plan(result.get('subtasks', []))

    print_worker_results(result.get('completed_tasks', []))

    print('\n\n')
    print('#'*80)
    print('Final Answer')
    print('#'*80)
    print()
    print(result.get('final_answer', ''))
    return result


TEST_CASES = [
    # ========================================================
    # EXAMPLE 1
    #
    # ★ 5개의 Dynamic Worker
    # ========================================================
    {
        "name": "Five-Part Agent Course Review",
        "question": (
            "지금까지 배운 Agent 과정을 "
            "다음 다섯 영역으로 나누어 평가해줘. "
            "각 영역은 서로 독립적으로 분석한 뒤 "
            "마지막에 하나의 학습 진단으로 합쳐줘. "
            "1) Tool Calling, "
            "2) RAG, "
            "3) Memory, "
            "4) Reflection, "
            "5) Multi-Agent. "
            "각 영역에서 배운 핵심과 "
            "다음에 보완할 점을 평가해줘."
        ),
        "audience": "instructor",
        "expected_subtask_count": 5,
        "expected_focus": (
            "Tool Calling / RAG / Memory / "
            "Reflection / Multi-Agent의 "
            "5개 독립 Worker 생성"
        ),
    },
    # ========================================================
    # EXAMPLE 2
    #
    # 3개 Worker
    # ========================================================
    {
        "name": "Router Handoff Supervisor",
        "question": (
            "Router, Handoff, Supervisor를 "
            "각각 하나의 독립 Subtask로 나누어 "
            "세 Worker가 동시에 분석하게 한 뒤 "
            "차이를 종합해줘."
        ),
        "audience": "intermediate",
        "expected_subtask_count": 3,
        "expected_focus": (
            "Router / Handoff / Supervisor를 "
            "3개 Worker로 분리"
        ),
    },
    # ========================================================
    # EXAMPLE 3
    #
    # 2개 Worker
    # ========================================================
    {
        "name": "Send and Reducer",
        "question": (
            "LangGraph Parallel Workflow를 "
            "두 가지 관점으로만 분석해줘. "
            "첫 번째 Worker는 "
            "Send API와 Custom State 구조를, "
            "두 번째 Worker는 "
            "Reducer와 Fan-In 구조를 "
            "독립적으로 설명하게 해줘."
        ),
        "audience": "intermediate",
        "expected_subtask_count": 2,
        "expected_focus": (
            "Send/Custom State와 "
            "Reducer/Fan-In의 2개 Subtask"
        ),
    },
    # ========================================================
    # EXAMPLE 4
    #
    # ★ 1개 Worker
    # ========================================================
    {
        "name": "One Integrated Task",
        "question": (
            "ToolRuntime의 State, Context, Store 관계를 "
            "여러 작업으로 나누지 말고 "
            "하나의 통합 Subtask로만 분석한 뒤 설명해줘."
        ),
        "audience": "intermediate",
        "expected_subtask_count": 1,
        "expected_focus": (
            "명시적으로 1개 Worker만 생성"
        ),
    },
    # ========================================================
    # EXAMPLE 5
    #
    # 4개 Worker
    # ========================================================
    {
        "name": "Parallel Architecture Risks",
        "question": (
            "Parallel Multi-Agent를 "
            "네 개의 독립 관점으로 분석해줘. "
            "1) 실행 구조, "
            "2) API 비용, "
            "3) Rate Limit, "
            "4) 결과 Merge 문제. "
            "각 관점은 별도 Worker가 맡고 "
            "마지막에 설계 가이드로 합쳐줘."
        ),
        "audience": "instructor",
        "expected_subtask_count": 4,
        "expected_focus": (
            "구조 / 비용 / Rate Limit / "
            "Merge의 4개 Worker"
        ),
    }
]

RUN_ALL_EXAMPLES = False

DEFAULT_EXAMPLE_INDEX = 0

if __name__ == "__main__":

    if RUN_ALL_EXAMPLES:

        for index, test in enumerate(TEST_CASES, start=1):
            print('\n\n')
            print('#'*80)
            print(f'Example {index}')
            print('#'*80)

            print(f'name: {test["name"]}')
            print('*'*80)
            run_planner_workers(
                question=test['question'],
                audience=test['audience'],
                expected_subtask_count=test['expected_subtask_count'],
                expected_focus=test['expected_focus'],
            )

    else:
        test = TEST_CASES[DEFAULT_EXAMPLE_INDEX]
        print(f'\n실행 예제: {test["name"]}')
        run_planner_workers(
            question=test['question'],
            audience=test['audience'],
            expected_subtask_count=test['expected_subtask_count'],
            expected_focus=test['expected_focus'],
        )