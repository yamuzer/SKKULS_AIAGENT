'''
supervisor -> worker(agent) 선택 ->

선택된 worker가 작업 -> supervisor -> 결과 확인 

-> 다음 worker 선택
'''

import json
import os

from typing import TypedDict, Literal
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = os.getenv(
    'GEMINI_MODEL',
    'gemini-3.7-flash'
)

if not GEMINI_API_KEY:
    raise RuntimeError('GEMINI_API_KEY가 없습니다.')


model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0,
    max_retries=2
)

# supervisor 설정

MAX_SUPERVISOR_ROUNDS = 8

MAX_WRITER_REVISIONS = 2

MIN_REVIEW_SCORE = 85



def get_response_text(
        response
):

    text = getattr(response, 'text', None)

    if isinstance(text, str) and text:
        return text

    content = response.content

    if isinstance(content, str):
        return content

    return str(content)


class SupervisorState(TypedDict):

    question: str
    audience: str


    # supervisor
    supervisor_round: int
    next_agent: str
    supervisor_reason: str
    delegated_task: str


    # research 
    research_done: bool
    research_count: int
    research_summary: str
    research_findings: list[str]
    research_cautions: list[str]


    # writer
    writer_done: bool
    writer_count: int
    draft_answer: str
    revision_count: int


    # reviewer
    review_done: bool
    reviewer_count: int
    review_passed: bool
    review_score: int
    review_strengths: list[str]
    review_issues: list[str]
    reviewer_feedback: str
    revision_instructions: list[str]


    # 실행 추적
    active_agent: str
    execution_order: list[str]
    route_history: list[dict]


    # 최종 결과
    final_answer: str



class SupervisorDecision(BaseModel):

    next_agent: Literal[
        'research_agent',
        'writer_agent',
        'reviewer_agent',
        'finish'
    ] = Field(
        description='현재 State를 보고 다음에 실행할 Worker 또는 작업 완료를 선택'
    )

    reason: str = Field(
        description='왜 해당 Worker 또는 Finish를 선택했는지 설명'
    )

    task_for_agent: str = Field(
        description='선택된 Worker가 다음에 수행해야 할 구체적인 작업. finish라면 빈 문자열'
    )

supervisor_model = model.with_structured_output(
    SupervisorDecision
)


SUPERVISOR_SYSTEM_PROMPT = """
당신은 Multi-Agent 시스템의 Supervisor입니다.

사용자에게 직접 답변하는 것이 주 역할이 아닙니다.

현재 Shared State를 보고 어떤 Worker가 다음 작업을 해야 하는지 결정합니다.

사용 가능한 Worker:

1. research_agent
2. writer_agent
3. reviewer_agent



======================================================
research_agent
======================================================

조사, 분석, 핵심 개념 정리, 주의점 정리가 필요한 경우 사용합니다.

다음과 같은 상황에 적합합니다.

- 기술 개념을 먼저 분석해야 함
- 비교를 위한 근거를 필요함
- 최종 글을 쓰기 전에 조사해야 함
- 사용자가 조사 결과만 요구함



======================================================
writer_agent
======================================================

최종 설명문, 강의 대본, 발표문, 정리된 답변 등을 작성할 때 사용합니다.


다음 상황에 적합합니다.

- Research 결과를 바탕으로 초안을 작성
- 사용자 완성된 콘텐츠를 요구
- Reviewer가 수정 지시를 보냄
- Draft를 다시 작성해야 함



======================================================
reviewer_agent
======================================================

작성된 Draft의 품질을 검토합니다.


다음 내용을 확인합니다.

- 사용자 질문을 제대로 해결했는가?
- Research 결과와 모순되지 않는가?
- 중요한 내용이 빠졌는가?
- 설명이 명확한가?
- 사용자의 대상 수준에 적합한가?


Dfrat가 존재한다면 최종 종료 전에 가능하면 Reviewer 검토를 수행하세요.



======================================================
일반적인 흐름
======================================================

기술적인 최종 설명 요청:

Research
-> Writer
-> Reviewer
-> Finish


Reviewer가 문제 발견:

Research
-> Writer
-> Reviewer
-> Writer
-> Reviewer
-> Finish


사용자가 조사만 요청:

Research
-> Finish


사용자가 주어진 문장만 다듬어 달라고 요청:

Writer
-> Reviewer
-> Finish


사용자가 기존 설명이 정확한지 검토만 요청:

Reviewer
-> Finish



======================================================
FINISH
======================================================

다음 경우 finish를 선택할 수 있습니다.

1. Reviewer가 통과시킨 Draft가 존재함.
2. 사용자가 Research 결과만 요구했고 Research가 완료됨.
3. 사용자가 검토만 요구했고 Reviewer 결과가 완료됨.



======================================================
중요
======================================================

이미 완료된 Worker를 이유 없이 반복 호출하지 마세요.

Research가 충분히 완료됐는데 똑같은 Research를 다시 시키지 마세요.

Reviewer가 Draft 문제를 지적했다면 다음에는 writer_agent에게 수정 작업을 맡기세요.

Writer가 수정한 뒤에는 다시 reviewer_agent에게 검토시키는 것이 좋습니다.

현재 Shared State를 가장 중요하게 판단하세요.
"""


# research structured output

class ResearchResult(BaseModel):

    summary: str = Field(
        description='질문에 대한 핵심 조사 요약'
    )

    findings: list[str] = Field(
        description='Writer가 활용해야 할 조사 결과'
    )

    caution_points: list[str] = Field(
        description='주의하거나 구분해서 설명해야 할 내용'
    )



# reviewer structured output

class ReviewResult(BaseModel):

    passed: bool = Field(
        description='현재 결과가 사용자에게 제공 가능한 수준이면 True'
    )

    score: int = Field(
        ge=0,
        le=100,
        description='현재 Draft의 품질 평가 점수'
    )

    strengths: list[str] = Field(
        description='현재 Draft에서 잘된 점'
    )

    issues: list[str] = Field(
        description='수정이 필요한 문제점'
    )

    revision_instructions: list[str] = Field(
        description='Writer가 수정해야 할 구체적인 지시'
    )

    summary: str = Field(
        description='전체 검토 결과 요약'
    )


research_model = model.with_structured_output(
    ResearchResult
)


reviewer_model = model.with_structured_output(
    ReviewResult
)


def build_research_answer(
        state: SupervisorState
): 

    lines = []
    lines.append('[조사 요약]')

    lines.append(
        state.get('research_summary')
    )
    lines.append('')

    lines.append('[핵심 조사 결과]')

    for finding in state.get('research_findings', []):
        lines.append(f'- {finding}')

    lines.append('')

    lines.append('[주의할 점]')
    cautions = state.get('research_cautions', [])

    if cautions:
        for caution in cautions:
            lines.append(f'- {caution}')

    else:
        lines.append('- 특별한 주의사항 없음')

    return '\n'.join(lines)



def build_review_report(
        state: SupervisorState
):

    lines = []

    lines.append('[검토 결과]')

    lines.append(
        f"점수: {state.get('review_score', 0)}"
    )

    lines.append(
        f"통과 여부: {state.get('review_passed', 0)}"
    )

    lines.append('')

    lines.append('[잘된 점]')

    for item in state.get('review_strengths', []):
        lines.append(f'- {item}')

    lines.append('')

    lines.append('[문제점]')

    issues = state.get('review_issues', [])

    if issues:
        for item in issues:
            lines.append(f'- {item}')

    else:
        lines.append('- 특별한 문제 없음')

    lines.append('')


    lines.append('[종합 의견]')

    lines.append(
        state.get('reviewer_feedback')
    )

    return '\n'.join(lines)


# supervisor가 종료할 때 사용할 답변 선택

def select_final_answer(
        state: SupervisorState
):

    draft = state.get('draft_answer', '')

    if draft:
        return draft

    # review only
    if state.get('review_done', False):
        return build_review_report(state)


    # research only
    if state.get('research_done', False):
        return build_research_answer(state)

    return '요청을 처리할 충분한 결과를 만들지 못했습니다.'



'''
supervisor node -> worker 선택 -> Command(goto=Worker)

... Worker 실행 -> static edge -> supervisor -> 반복
'''

def supervisor_node(
        state: SupervisorState
) -> Command[
    Literal[
        'research_agent',
        'writer_agent',
        'reviewer_agent',
        '__end__'
    ]
]:
    print('\n')
    print('='*80)
    print('[Supervisor 실행]')
    print('='*80)

    current_round = state.get('supervisor_round', 0) + 1

    print(f'Supervisor Round: {current_round}')
    print(f"Research Done: {state.get('research_done', False)}")
    print(f"Writer Done: {state.get('writer_done', False)}")
    print(f"Review Done: {state.get('review_done', False)}")
    print(f"Review Passed: {state.get('review_passed', False)}")
    print(f"Revision Count: {state.get('revision_count')}")


    # reivewer 통과 후에는 종료
    if (
        state.get('review_done', False)
        and
        state.get('review_passed', False)
    ):
        print('\n[Supervisior Hard Rule]')
        print('Reviewer PASS -> FINISH')

        history_item = {
            'round': current_round,
            'next_agent': 'finish',
            'reason': 'Reviewer가 품질 기준을 통과시켰습니다.'
        }

        return Command(
            update={
                'supervisor_round': current_round,
                'next_agent': 'finish',
                'supervisor_reason': 'Reviewer가 품질 기준을 통과시켰습니다.',
                'delegated_task': '',
                'active_agent': 'supervisor',
                'route_history': [
                    *state.get('route_history', []),
                    history_item
                ],
                'execution_order': [
                    *state.get('execution_order', []),
                    'supervisor'
                ],
                'final_answer': select_final_answer(state)
            },

            goto=END
        )


    if (
            state.get('review_done', False)
            and
            state.get('review_passed', False)
            and
            state.get('draft_answer', '')
            and
            state.get('revision_count', 0) >= MAX_WRITER_REVISIONS
        ):
            print('\n[Supervisior Hard Rule]')
            print('Maximum Revision -> FINISH')

            final_text = (
                state.get('draft_answer', '') 
                +
                '\n\n'
                '[검토 참고] '
                '최대 수정 횟수에 도달하여 현재 초안으로 종료합니다. '
                f'마지막 검토 점소: {state.get("review_score", 0)}'
            )

            return Command(
                    update={
                        'supervisor_round': current_round,
                        'next_agent': 'finish',
                        'supervisor_reason': '최대 Writer 수정 횟수에 도달했습니다.',
                        'active_agent': 'supervisor',
                        'route_history': [
                            *state.get('route_history', []),
                            {
                                'round': current_round,
                                'next_agent': 'finish',
                                'reason': '최대 Writer 수정 횟수에 도달했습니다.'
                            }
                        ],
                        'execution_order': [
                            *state.get('execution_order', []),
                            'supervisor'
                        ],
                        'final_answer': final_text
                    },
        
                    goto=END
                )



    if current_round > MAX_SUPERVISOR_ROUNDS:
        print('\n[Supervisor Limit]')
        print('Maximum Supervisor Round -> END')

        return Command(
                update={
                    'supervisor_round': current_round,
                    'next_agent': 'finish',
                    'supervisor_reason': '최대 반복 횟수에 도달했습니다.',
                    'active_agent': 'supervisor',
                    'execution_order': [
                        *state.get('execution_order', []),
                        'supervisor'
                    ],
                    'final_answer': select_final_answer(state)
                },
    
                goto=END
            )


    # supervisor에게 보여줄 State Summary

    state_summary = {
        'question': state['question'],
        'audience': state['audience'],
        'research_done': state.get('research_done', False),
        'research_summary': state.get('research_summary', ''),
        'write_done': state.get('writer_done', False),
        'draft_answer': state.get('draft_answer', ''),
        'review_done': state.get('review_done', False),
        'review_passed': state.get('review_passed', False),
        'review_score': state.get('review_score', 0),
        'review_issues': state.get('review_issues', []),
        'reviewer_feedback': state.get('reviewer_feedback', ''),
        'revision_count': state.get('revision_count', 0)
    }

    decision = supervisor_model.invoke(
        [
            SystemMessage(
                content=SUPERVISOR_SYSTEM_PROMPT
            ),
            HumanMessage(
                content=f"""
현재 Multi-Agent Shared State:

{
    json.dumps(
        state_summary,
        ensure_ascii=False,
        indent=2
    )
}


다음에 실행할 Worker를 결정하세요.

더 이상 Worker가 필요하지 않다면 finish를 선택하세요.
"""
            )
        ]
    )

    print('\n[Supervisor Decision]')
    print(f'Next Agent: {decision.next_agent}')
    print(f'Reason: {decision.reason}')
    print(f'Task: {decision.task_for_agent}')

    history_item = {
        'round': current_round,
        'next_agent': decision.next_agent,
        'reason': decision.reason
    }

    execution_order = [
        *state.get('execution_order', []),
        'supervisor'
    ]


    if decision.next_agent == 'finish':

        return Command(
            update={
                'supervisor_round': current_round,
                'next_agent': 'finish',
                'supervisor_reason': decision.reason,
                'delegated_task': '',
                'active_agent': 'supervisor',
                'route_history':[
                    *state.get('route_history', []),
                    history_item
                ],
                'execution_order': execution_order,
                'finish_answer': select_final_answer(state)
            },
            goto=END
        )


    return Command(
        update={
            'supervisor_round': current_round,
            'next_agent': decision.next_agent,
            'supervisor_reason': decision.reason,
            'delegated_task': decision.task_for_agent,
            'active_agent': decision.next_agent,
            'route_history':[
                *state.get('route_history', []),
                history_item
            ],
            'execution_order': execution_order
        },
        goto=decision.next_agent
    )


# research agent prompt

RESEARCH_AGENT_PROMPT = """
당신은 Supervisor가 관리하는 Research Agent입니다.

당신의 역할은 조사와 분석입니다.

최종 사용자용 대본을 작성하는 것이 목적이 아닙니다.



=========================================================
수행 내용
=========================================================

1. 사용자 질문의 핵심을 분석하세요.
2. Writer가 사용할 핵심 사실과 개념을 정리하세요.
3. 서로 혼동할 수 있는 개념은 구분하세요.
4. 설명 시 주의점을 정리하세요.



=========================================================
중요
=========================================================

Supervisor가 전달한 delegated_task를 우선 수행하세요.

현재 예제는 교육용 AI / Agent 수업 문맥입니다.

최신 외부 사실이 필요한 질문에서 검증되지 않는 구체적 정보를 만들어내지 마세요.
"""



def research_agent_node(
        state: SupervisorState
):

    print('\n')
    print('='*80)
    print('[Reseach Agent 실행]')
    print('='*80)

    print(f'\n[Delegated Task] : {state.get("delegated_task",'')}')


    response = research_model.invoke(
        [
            SystemMessage(
                content=RESEARCH_AGENT_PROMPT
            ),
            HumanMessage(
                content=(
                    f"""
사용자의 질문:

{state["question"]}


대상 수준:

{state["audience"]}


Supervisor가 전달한 작업:

{state.get("delegated_task", "")}


다음 Writer 또는 Supervisor가 활용할 수 있도록 조사 결과를 구조화하세요.
"""
                )
            )
        ]
    )

    print('\n[Research Summary]')
    print(response.summary)

    print('\n[Findings]')

    for item in response.findings:
        print(f'- {item}')


    return {
        'research_done': True,
        'research_count':(
            state.get('research_count', 0) + 1
        ),
        'research_summary': response.summary,
        'research_findings': response.findings,
        'research_cautions': response.caution_points,
        'active_agent': 'research_agent',
        'execution_order': [
            *state.get('execution_order', []),
            'research_agent'
        ]
    }



#############################################
# Writer Agent Prompt
#############################################

WRITER_AGENT_PROMPT = """
당신은 Supervisor가 관리하는 Writer Agent입니다.

당신의 역할은 사용자가 실제로 읽거나 수업에서 사용할 최종 Draft를 작성하는 것입니다.



==================================================================
Research 결과가 있다면
==================================================================

Research Agent의:

summary
findings
caution_points

를 적극적으로 활용하세요.



==================================================================
Reviewer Feedback이 있다면
==================================================================

이전 Draft를 그대로 반복하지 마세요.

Reviewer가 지적한 issues와 revision_instructions를 반영하여 수정하세요.



==================================================================
AUDIENCE
==================================================================

beginner:
쉬운 표현과 예를 사용합니다.

intermediate:
기술 용어와 Workflow를 설명하세요.

instructor:
수업에서 사용할 수 있도록 개념 차이와 학생이 헷갈릴 부분을 강조합니다.



==================================================================
중요
==================================================================

Supervisor가 전달한 작업을 우선 수행하세요.

사용자의 요구 형태를 반드시 따르세요.

예:

5분 강의 멘트
-> 실제 강의 문장

핵심 설명
-> 설명문

비교
-> 비교가 명확한 구조
"""


def writer_agent_node(
        state: SupervisorState
):
    print('\n')
    print('='*80)
    print('[Writer Agent 실행]')
    print('='*80)

    previous_draft = state.get('draft_answer', '')
    reviewer_feedback = state.get('reviewer_feedback', '')
    revision_instructions = state.get('revision_instructions', [])

    is_revision = (
        bool(previous_draft) 
        and
        state.get('review_done', False)
        and
        not state.get('review_passed')
    )

    print(f'\nRevision Mode: {is_revision}')

    question = state['question']
    audience = state['audience']

    prompt = f"""
사용자의 질문:

{question}


대상 수준:

{audience}


Supervisor가 전달한 작업:

{state.get("delegated_task", "")}



==================================================================
Research 결과
==================================================================

Summary:

{state.get("research_summary", "")}


Findings:

{
    json.dumps(
        state.get('research_findings', []),
        ensure_ascii=False,
        indent=2
    )
}


Caution Points:

{
    json.dumps(
        state.get('research_cautions', []),
        ensure_ascii=False,
        indent=2
    )
}



==================================================================
기존 Draft
==================================================================

{previous_draft}



==================================================================
Reviewer Feedback
==================================================================

{reviewer_feedback}



==================================================================
Revision Instructions
==================================================================

{
    json.dumps(
        revision_instructions,
        ensure_ascii=False,
        indent=2
    )
}


현재 상황에 맞게 최종 Draft를 작성하세요.
"""

    
    
    response = model.invoke(
        [
            SystemMessage(
                content=WRITER_AGENT_PROMPT
            ),
            HumanMessage(
                content=prompt
            )
        ]
    )

    text = get_response_text(response)

    print('\n[Writer Draft]')
    print(text)


    revision_count = state.get('revision_count', 0)

    if is_revision:
        revision_count += 1

    return {
        'writer_done': True,
        'writer_count':(
            state.get('writer_count', 0) + 1
        ),
        'draft_answer': text,
        'revision_count': revision_count,
        'review_done': False,
        'review_passed': False,
        'review_score': 0,
        'review_strengths': [],
        'review_issues': [],
        'reviewer_feedback': '',
        'revision_instructions': [],
        'active_agent': 'writer_agent',
        'execution_order': [
            *state.get('execution_order', []),
            'writer_angent'
        ]
    }



REVIEWER_AGENT_PROMPT = f"""
당신은 Supervisor가 관리하는 Reviewer Agent입니다.

Writer Agent가 작성한 결과를 검토합니다.


==================================================================
검토 기준
==================================================================

1. 사용자의 질문에 직접 답했는가?
2. Research 결과가 있다면 Research 내용과 충돌하지 않는가?
3. 중요한 내용이 빠져 있지 않는가?
4. 설명이 명확한가?
5. 사용자의 audience에 적절한가?
6. 요청한 출력 형태를 지켰는가?


==================================================================
PASS 기준
==================================================================

score >= {MIN_REVIEW_SCORE}

그리고 중요한 문제 없어야 합니다.



==================================================================
FAIL
==================================================================

수정이 필요하다면:

passed = false

issues에 문제를 기록하고

revision_instructions에 Writer가 실제로 수정할 수 있는 구체적인 지시를 작성하세요.



==================================================================
중요
==================================================================

단순 취향 차이 때문에 불필요하게 Fail시키지 마세요.

실질적인 품질 문제를 중심으로 평가하세요.
"""



def reviewer_agent_node(
        state: SupervisorState
):
    print('\n')
    print('='*80)
    print('[Reviewer Agent 실행]')
    print('='*80)

    draft = state.get('draft_answer', '')

    question = state['question']
    audience = state['audience']

    if draft:
        content_to_review = draft

    else:
        content_to_review = question

    
    response = reviewer_model.invoke(
        [
            SystemMessage(
                content=REVIEWER_AGENT_PROMPT
            ),
            HumanMessage(
                content=f"""
사용자의 원래 요청:

{question}


대상:

{audience}


Research Summary

{state.get("research_summary", "")}


Research Findings:
{
    json.dumps(
        state.get("research_findings", []),
        ensure_ascii=False,
        indent=2
    )
}



검토할 내용:

{content_to_review}


현재 결과를 검토하세요.
"""
            )
        ]
    )

    passed = (
        response.passed
        and
        response.score >= MIN_REVIEW_SCORE
        and
        len(response.issues) == 0
    )

    print('\n[Review Result]')
    print(f'Passed: {passed}')
    print(f'Score: {response.score}')

    print('Issues:')

    if response.issues:
        for issue in response.issues:
            print(f'- {issue}')

    else:
        print('- 없음')

    print('\nRevision Instructions:')

    if response.revision_instructions:
        for item in response.revision_instructions:
            print(f'- {item}')

    else:
        print('- 없음')


    updates = {
        'review_done': True,
        'reviewer_count': (
            state.get('reviewer_count', 0) + 1
        ),
        'review_passed': passed,
        'review_score': response.score,
        'review_issues': response.issues,
        'reviewer_feedback': response.summary,
        'revision_instructions': response.revision_instructions,
        'active_agent': 'reviewer_agent',
        'execution_order': [
            *state.get('execution_order', []),
            'reviewer_agent'
        ]
    }

    if not draft:
        temporary_state = {
            **state,
            **updates
        }

        updates['final_answer'] = build_review_report(temporary_state)

    return updates



builder = StateGraph(SupervisorState)


builder.add_node(
    'supervisor',
    supervisor_node
)

builder.add_node(
    'research_agent',
    research_agent_node
)

builder.add_node(
    'writer_agent',
    writer_agent_node
)

builder.add_node(
    'reviewer_agent',
    reviewer_agent_node
)





builder.add_edge(
    START,
    'supervisor'
)

builder.add_edge(
    'research_agent',
    'supervisor'
)

builder.add_edge(
    'writer_agent',
    'supervisor'
)

builder.add_edge(
    'reviewer_agent',
    'supervisor'
)

supervisor_graph = builder.compile()


def run_supervisor(
        question: str,
        audience: str,
        expected_flow: str
):

    print('\n\n')
    print('='*80)
    print('[Multi Agent Ex3]')
    print('='*80)

    print(f'\nquestion: {question}')
    print(f'\naudience: {audience}')
    print(f'\nexpected_flow: {expected_flow}')


    initial_state = {
        'question': question,
        'audience': audience,
        'supervisor_round': 0,
        'next_agent': '',
        'supervisor_reason': '',
        'delegated_task': '',
        'research_done': False,
        'research_count': 0,
        'research_summary': '',
        'research_findings': [],
        'research_cautions': [],
        'writer_done': False,
        'writer_count': 0,
        'draft_answer': '',
        'revision_count': 0,
        'review_done': False,
        'reviewer_count': 0,
        'review_passed': False,
        'review_score': 0,
        'review_strengths': [],
        'review_issues': [],
        'reviewer_feedback': '',
        'revision_instructions': [],
        'active_agent': 'supervisor',
        'route_history': [],
        'final_answer': '',
        'execution_order': []
    }


    result = supervisor_graph.invoke(
        initial_state,
        config={
            'recursion_limit': 30
        }
    )

    print('\n')
    print('#'*80)
    print('Execution Summary')
    print('#'*80)

    print('\nExecution Order:')
    print(' -> '.join(result['execution_order'])) 

    print(f'\nSupervisor Rounds: {result["supervisor_round"]}')
    print(f'\nResearch Count: {result["research_count"]}')
    print(f'\nWriter Count: {result["writer_count"]}')
    print(f'\nReviewer Count: {result["reviewer_count"]}')
    print(f'\nRevision Count: {result["revision_count"]}')
    print(f'\nFinal Review Score: {result["review_score"]}')
    print(f'\nFinal Review Passed: {result["review_passed"]}')


    # supervisor decision history

    print('\n')
    print('='*80)
    print('Supervisor Route History')
    print('='*80)

    for route in result['route_history']:
        print(f'\nRound: {route.get("round")}')
        print(f'Next: {route.get("next_agent")}')
        print(f'Reason: {route.get("reason")}')
    

    print('\n\n')
    print('='*80)
    print('[Final Answer]')
    print('='*80)

    print(result['final_answer'])

    return result


TEST_CASES = [
    {
        'name': 'Technical Explanation',
        'question': (
            'Router, Handoff, Supervisor의 차이를 학생들에게 설명 할 수 있도록 '
            '예시까지 포함해서 정리해줘.'
        ),
        'audience': 'instructor',
        'expected_flow': (
            'supervisor -> research_agent -> supervisor -> writer_agent '
            '-> supervisor -> reviewer_agent -> supervisor -> finish'
        )
    },

    {
        'name': 'Research only',
        'question': (
            'Supervisor 패턴의 장점과 단점, 적용 시 주의점을 조사해줘. '
            '최종 강의문은 만들지 말고 조사 포인트만 정리해줘.'
        ),
        'audience': 'instructor',
        'expected_flow': (
            'supervisor -> research_agent -> supervisor ->  finish'
        )
    },

    {
        'name': 'Direct Writer',
        'question': (
            '다음 문장을 오프닝 멘트로 자연 스럽게 다듬어줘.\n\n'
            '"오늘은 멀티에이전트를 보겠습니다. 여러 에이전트가 같이 일을 합니다."'
        ),
        'audience': 'instructor',
        'expected_flow': (
            'supervisor -> writer_agent -> supervisor -> '
            'reviewer_agent -> supervisor -> finish'
        )
    },

    {
        'name': 'Review Only',
        'question': (
            '다음 설명이 개념적으로 적절한지 검토만 해줘.\n\n'
            '"Router는 처음 요청을 분류하는 역할이고, Supervisor는 Worker '
            '결과 다시 받아 다음 작업을 반복 결정할 수 있다."'
        ),
        'audience': 'intermediate',
        'expected_flow': (
            'supervisor -> reviewer_agent -> supervisor -> finish'
        )
    },

    {
        'name': 'Lecture with Review',
        'question': (
            'Multi-Agent의 Router와 Supervisor 차이를 학생들에게 설명하는 '
            '5분 강의 멘트를 만들어줘. 최종적으로 내용이 정확하고 이해하기 '
            '쉬운지도 검토해줘.'
        ),
        'audience': 'intermediate',
        'expected_flow': (
            'supervisor -> research_agent -> writer_agent -> reviewer_agent '
            '-> 필요 시 writer revision -> reviewer_agent -> finish'
        )
    },

    
]

RUN_ALL_EXAMPLES = False

DEFAULT_EXAMPLE_INDEX = 4

if __name__ == '__main__':

    if RUN_ALL_EXAMPLES:
        for index, test in enumerate(TEST_CASES, start=1):
            print('\n\n')
            print('='*80)
            print(f'Example {index}')
            print('='*80)

            print(test['name'], end='\n\n')

            run_supervisor(
                question=test['question'],
                audience=test['audience'],
                expected_flow=test['expected_flow']
            )

    else:

        test = TEST_CASES[DEFAULT_EXAMPLE_INDEX]
        print(test['name'], end='\n\n')
        
        run_supervisor(
            question=test['question'],
            audience=test['audience'],
            expected_flow=test['expected_flow']
        )
