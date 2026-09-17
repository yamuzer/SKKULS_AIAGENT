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



class RouterState(TypedDict):

    # 사용자 입력:
    question: str
    audience: str

    # router 결과
    selected_agent: str
    route_reason: str
    route_confidence: int
    routed_task: str


    # 실행 정보
    active_agent: str
    execution_order: str


    #최종 답변
    final_answer: str



# router structured output
# selected_agent, reason, confidence, task

class RouterDecision(BaseModel):

    selected_agent: Literal[
        'research_agent',
        'writer_agent',
        'explainer_agent'
    ] = Field(
        description='사용자 질문을 처리하기 가장 적합한 Agent'
    )


    reason: str = Field(
        description='해당 Agent를 선택한 이유'
    )


    confidence: int = Field(
        ge=0,
        le=100,
        description=(
            'Routing 판단에 대한 확신 정도. '
            'Truth probability가 아니라 Router의 판단 지표'
        )
    )


    task_for_agent: str = Field(
        description='선택된 Agent가 수행해야 할 구체적인 작업'
    )


router_model = model.with_structured_output(
    RouterDecision
)


ROUTER_SYSTEM_PROMPT = """
당신은 Multi-Agent 시스템의 Router입니다.

직접 사용자 질문에 답하지 않습니다.

당신의 역할은 사용자 요청을 분석하여
가장 적합한 전문 Agent 하나를 선택하는 것입니다.

사용 가능한 Agent는 세 개입니다.


==========================================================
1. research_agent
==========================================================

분석, 조사, 핵심 포인트 정리,
판단 기준 정리 등이 필요한 경우 선택합니다.

특히 사용자가:

"조사해줘"
"분석해줘"
"핵심 포인트만"
"주의점만"
"자료를 만들기 전에 분석"
"답안은 아직 만들지마"

등을 요청하면 research_agent가 적합합니다.


예:

"Multi-Agent의 장단점을 조사해줘."
"Reflection Agent의 핵심 개념과 주의점만 분석해줘."
"최종 설명은 필요없고 Router와 Handoff의 차이만 조사해줘."



==========================================================
2. writer_agent
==========================================================

사용자가 바로 사용할 수 있는 완성된 결과물이 필요한 경우 선택합니다.

예:

강의 멘트
발표 대본
최종 설명문
수업용 문장
교육 자료용 문장
완성된 요약본
발표용 원고


사용자가:

"작성해줘"
"대본으로 만들어줘"
"5분 발표 멘트"
"최종 설명문"
"수업에서 그대로 말할 수 있게"

등을 요청하면 writer_agent가 적합합니다.


예:

"Reflection Agent를 5분 설명 멘트로 작성해줘."
"LangGraph, State, Node, Edge 설명을 발표 대본으로 만들어줘."



==========================================================
3. explainer_agent
==========================================================

사용자가 어떤 개념 자체를 이해하려는 경우 선택합니다.

특히:

"뭐야?"
"왜?"
"차이가 뭐야?"
"어떻게 동작해?"
"쉽게 설명해줘."
"예를 들어 설명해줘"

같은 질문에 적합합니다.


예:
"Router와 Handoff의 차이가 뭐야?"
"ToolRuntime이 왜 필요한지 설명해줘."
"Agentic RAG가 어떻게 동작하는지 알려줘."



==========================================================
중요한 구분
==========================================================

다음 질문:

"Reflection Agent가 뭐야?"
-> explainer_agent


다음 질문:
"Reflection Agent의 장단점과 수업 시 주의점을 조사해줘."
-> research_agent


다음 질문:
"Reflection Agent를 설명하는 5분 멘트를 작성해줘."
-> writer_agent



==========================================================
애매한 경우
==========================================================

사용자의 최종 목적을 가장 중요하게 판단하세요.

정보를 이해하려는 목적:
-> explainer_agent

정보를 분석하거나 준비하려는 목적:
-> research_agent

완성된 콘텐츠를 만들려는 목적:
-> writer_agent



==========================================================
출력
==========================================================

selected_agent에는 반드시:

research_agent
writer_agent
explainer_agent

중 하나만 선택하세요.

task_for_agent에는 선택된 Agent가 무엇을 수행해야 하는지 명확하게 정리하세요.
"""


def router_node(
        state: RouterState
) -> Command[
    Literal[
        'research_agent',
        'writer_agent',
        'explainer_agent'
    ]
]:

    print('\n')
    print('='*80)
    print('[Router 실행]')
    print('='*80)

    question = state['question']
    audience = state['audience']

    print('\nquestion')
    print(question)

    print(f'\naudience: {audience}')


    decision = router_model.invoke(
        [
            SystemMessage(
                content=ROUTER_SYSTEM_PROMPT
            ),
            HumanMessage(
                content=f"""
사용자 질문:

{question}


사용자 수준:

{audience}

이 요청을 처리할 가장 적합한 전문 Agent 하나를 선택하세요.
"""
            )
        ]
    )

    print('\n[Routing Result]')
    print(f'Selected Agent: {decision.selected_agent}')
    print(f'Confidence: {decision.confidence}')
    print(f'Reason: {decision.reason}')
    print(f'Task: {decision.task_for_agent}')


    return Command(
        update={
            'selected_agent': decision.selected_agent,
            'route_reason': decision.reason,
            'route_confidence': decision.confidence,
            'routed_task': decision.task_for_agent,
            'active_agent': decision.selected_agent,
            'execution_order': [
                *state.get('execution_order', []),
                'router'
            ]
        },
        goto=decision.selected_agent
    )




# Research Agent Prompt
RESEARCH_AGENT_PROMPT = """
당신은 Research Agent입니다.

사용자에게 보여줄 화려한 최종 콘텐츠를 만드는 것보다
질문을 분석하고 핵심 자료를 구조화하는 것이 목적입니다.


===============================================================
수행 내용
===============================================================

1. 질문의 핵심 목적을 분석하세요.
2. 중요한 개념을 분리하세요.
3. 핵심 조사 결과를 정리하세요.
4. 개념상 주의해야 할 점을 정리하세요.
5. 필요하면 적용 기준도 제시하세요.


===============================================================
출력 형식
===============================================================

다음 구조를 권장합니다.

[조사 목적]

[핵심 개념]

[주요 분석]

[주의할 점]

[정리]



===============================================================
중요
===============================================================

사용자가 조사만 요청했다면
발표 대본이나 완성된 강의문으로 바꾸지 마세요.

구체적인 외부 최신 사실이 필요한 질문에서는 근거 없이 사실을 만들어내지 마세요.
"""




def research_agent_node(
        state: RouterState
):

    print('\n')
    print('='*80)
    print('[Reseach Agent 실행]')
    print('='*80)

    print(f'\n[routed task] : {state["routed_task"]}')


    response = model.invoke(
        [
            SystemMessage(
                content=RESEARCH_AGENT_PROMPT
            ),
            HumanMessage(
                content=(
                    f"""
사용자의 원래 질문:

{state["question"]}


Router가 전달한 작업:

{state["routed_task"]}


답변 대상 수준:

{state["audience"]}


Research Agent의 역할에 맞게 조사 및 분석 결과를 작성하세요.
"""
                )
            )
        ]
    )

    text = get_response_text(response)

    print('\n[Research Result]')
    print(text)

    return {
        'final_answer': text,
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
당신은 Writer Agent입니다.

사용자가 실제로 사용할 수 있는 완성된 콘텐츠를 작성하는 것이 목적입니다.


==================================================================
주요 작업
==================================================================

- 강의 멘트
- 발표 대본
- 완성된 설명문
- 수업 자료용 문장
- 발표용 원고
- 교육용 요약문


==================================================================
 audience
==================================================================

beginner:
- 쉬운 표현
- 비유와 간단한 예
- 전문 용어를 바로 풀어서 설명

intermediate:
- 핵심 용어 사용
- 구조와 동작 과정 설명
- 간단한 예 포함

instructor:
- 수업에서 설명할 수 있도록
- 개념 차이와 교육 포인트 강조
- 학생이 혼동할 부분까지 설명


==================================================================
중요
==================================================================

사용자의 요구 형태를 반드시 따르세요.

예:

"5분 발표 멘트"

라고 했다면 분석 보고서가 아니라 실제 발표할 수 있는 문장 형태로 작성한다.

"수업에서 그대로 설명"

이라고 했다면 강사의 발화 형태를 고려합니다.
"""


def writer_agent_node(
        state: RouterState
):
    print('\n')
    print('='*80)
    print('[Writer Agent 실행]')
    print('='*80)

    routed_task = {state["routed_task"]}
    print(f'\n[Router Task]: {routed_task}')

    question = state['question']
    audience = state['audience']
    
    response = model.invoke(
        [
            SystemMessage(
                content=WRITER_AGENT_PROMPT
            ),
            HumanMessage(
                content=f"""
사용자의 원래 질문:

{question}


Router가 전달한 작업:

{routed_task}


대상 수준:

{audience}


사용자가 바로 활용할 수 있는 완성된 결과물을 작성하세요
"""
            )
        ]
    )

    text = get_response_text(response)

    print('\n[Writer Result]')
    print(text)

    return {
        'final_answer': text,
        'active_agent': 'writer_agent',
        'execution_order': [
            *state.get('execution_order', []),
            'writer_agent'
        ]
    }



EXPLAINER_AGENT_PROMPT = """
당신은 Explainer Agent입니다.

사용자가 기술 개념을 정확하게 이해할 수 있도록 설명하는 것이 목적입니다.



==================================================================
설명 원칙
==================================================================

1. 먼저 핵심 정의를 설명하세요.
2. 왜 필요한지 설명하세요.
3. 어떻게 동작하는지 설명하세요.
4. 가능하면 간단한 예를 사용하세요.
5. 비슷한 개념과 헷갈릴 경우 차이를 구분하세요.


==================================================================
audience
==================================================================

beginner:

- 쉬운 단어
- 간단한 비유
- 단계적인 설명을 사용하세요


intermediate:

- 정확한 기술 용어와 Workflow를 설명하세요.


instructor:

- 학생에게 어떻게 설명해야 하는지,
- 어디에서 혼동할 수 있는지도 포함하세요.



==================================================================
중요
==================================================================

단순히 정의 한 줄로 끝내지 마세요.

사용자가 "왜?", "어떻게?"를 물었다면 원인과 동작 과정을 분리해서 설명하세요.
"""



def explainer_agent_node(
        state: RouterState
):
    print('\n')
    print('='*80)
    print('[Explainer Agent 실행]')
    print('='*80)

    routed_task = {state["routed_task"]}
    print(f'\n[Router Task]: {routed_task}')

    question = state['question']
    audience = state['audience']
    
    response = model.invoke(
        [
            SystemMessage(
                content=EXPLAINER_AGENT_PROMPT
            ),
            HumanMessage(
                content=f"""
사용자의 원래 질문:

{question}


Router가 전달한 작업:

{routed_task}


대상 수준:

{audience}


사용자가 개념을 이해할 수 있도록 체계적으로 설명하세요.
"""
            )
        ]
    )

    text = get_response_text(response)

    print('\n[Explainer Result]')
    print(text)

    return {
        'final_answer': text,
        'active_agent': 'explainer_agent',
        'execution_order': [
            *state.get('execution_order', []),
            'explainer_agent'
        ]
    }



builder = StateGraph(RouterState)


builder.add_node(
    'router',
    router_node
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
    'explainer_agent',
    explainer_agent_node
)





builder.add_edge(
    START,
    'router'
)

builder.add_edge(
    'research_agent',
    END
)

builder.add_edge(
    'writer_agent',
    END
)

builder.add_edge(
    'explainer_agent',
    END
)

router_graph = builder.compile()


def run_router(
        question: str,
        audience: str,
        expected_agent: str,
        expected_reason: str
):

    print('\n\n')
    print('='*80)
    print('[Multi Agent Ex2]')
    print('='*80)

    print(f'\nquestion: {question}')
    print(f'\naudience: {audience}')
    print(f'\nexpected_agent: {expected_agent}')
    print(f'\nexpected_reason: {expected_reason}')

    initial_state = {
        'question': question,
        'audience': audience,
        'selected_agent': '',
        'route_reason': '',
        'route_confidence': 0,
        'routed_task': '',
        'active_agent': '',
        'final_answer': '',
        'execution_order': []
    }


    result = router_graph.invoke(
        initial_state,
        config={
            'recursion_limit': 10
        }
    )

    print('\n')
    print('#'*80)
    print('Routing Summary')
    print('#'*80)

    print('\nExpected Agent:')
    print(expected_agent)

    print('\nActual Agent:')
    print(result['selected_agent'])

    print(f'\nConfidence: {result["route_confidence"]}')
    print(f'\nReason: {result["route_reason"]}')
    print(f'\nRouted Task:\n{result["routed_task"]}')

    print('\nExecution Order:')
    print(' -> '.join(result['execution_order']))

    print('\n\n')
    print('='*80)
    print('[Final Answer]')
    print('='*80)

    print(result['final_answer'])

    return result


TEST_CASES = [
    {
        'name': 'RAG Explanation',
        'question': 'RAG가 무엇인지 AI를 처음 배우는 학생도 이해할 수 있도록 설명해줘.',
        'audience': 'beginner',
        'expected_agent': 'explainer_agent',
        'expected_reason': '특정 개념을 이해하려는 설명형 질문'
    },

    {
        'name': 'Multi-Agent Research',
        'question': (
            'Multi-Agent를 사용하는 장점과 단점, 그리고 도입할 때 주의할 점을 조사해줘.'
            '아직 강의문은 만들지 마.'
        ),
        'audience': 'instructor',
        'expected_agent': 'research_agent',
        'expected_reason': '최종 콘텐츠가 아니라 분석과 조사 포인트를 요청'
    },

    {
        'name': 'Reflection Lecture Script',
        'question': (
            'Reflection Agent를 학생들에게 설명할 수 있도록 '
            '5분 분량의 강의 멘트를 작성해줘.'
        ),
        'audience': 'instructor',
        'expected_agent': 'writer_agent',
        'expected_reason': '완성된 강의 멘트라는 결과물을 요구'
    },
]

RUN_ALL_EXAMPLES = False

DEFAULT_EXAMPLE_INDEX = 0

if __name__ == '__main__':

    if RUN_ALL_EXAMPLES:
        for index, test in enumerate(TEST_CASES, start=1):
            print('\n\n')
            print('='*80)
            print(f'Example {index}')
            print('='*80)

            print(test['name'], end='\n\n')

            run_router(
                question=test['question'],
                audience=test['audience'],
                expected_agent=test['expected_agent'],
                expected_reason=test['expected_reason']
            )

    else:

        test = TEST_CASES[DEFAULT_EXAMPLE_INDEX]
        print(test['name'], end='\n\n')
        
        run_router(
            question=test['question'],
            audience=test['audience'],
            expected_agent=test['expected_agent'],
            expected_reason=test['expected_reason']
        )
