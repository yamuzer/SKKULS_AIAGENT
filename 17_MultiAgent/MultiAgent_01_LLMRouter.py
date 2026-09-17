import json
import os

from typing import TypedDict
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ENV_PATH = BASE_DIR / "../.env"
load_dotenv(dotenv_path=ENV_PATH)

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

'''
question -> 
Research Agent:  
[state 저장, research_summary, key_concepts, findings, caution option]


-> Writer Agent 읽음 -> final_answer
'''

class MultiAgentState(TypedDict):
    question: str

    # 답변 대상 수준
    # beginner, intermediate, instructor
    audience: str


    # Research Agent 결과
    research_summary: str

    key_concepts: list[str]

    findings: list[str]

    caution_points: list[str]

    recommended_structure: list[str]


    # Writer Agent 결과

    final_answer: str


    # 어떤 Agent가 실행되었는지 확인

    execution_order: list[str]



# Research Agent 출력 Schema
# summary, concepts, findings, caution

class ResearchResult(BaseModel):

    summary: str = Field(
        description='질문의 핵심을 정리한 조사 요약'
    )

    key_concepts: list[str] = Field(
        description='질문을 이해하기 위해 필요한 핵심 개념'
    )

    findings: list[str] = Field(
        description='최종 답변에 포함할 주요 조사 결과'
    )

    caution_points: list[str] = Field(
        description='오해하기 쉬운 부분, 구분해야 할 개념, 주의해서 설명해야 할 내용'
    )

    recommended_structure: list[str] = Field(
        description='Writer Agent가 최종 답변을 구성할 때 권장되는 설명 순서'
    )


research_model = model.with_structured_output(
    ResearchResult
)



# Research Agent Prompt
RESEARCH_AGENT_PROMPT = """
당신은 Research Agent입니다.

당신의 역할은 사용자에게 완성된 최종 답변을 작성하는 것이 아닙니다.

다음 Writer Agent가 좋은 답변을 작성할 수 있도록 질문을 분석하고 핵심 정보를 구조하는 것이
목적입니다.



[역할]

1. 질문의 핵심 의도를 분석하세요.
2. 필요한 핵심 개념을 분리하세요.
3. 최종 답변에서 반드시 설명해야 할 사실을 정리하세요.
4. 서로 혼동하기 쉬운 개념이 있으면 구분하세요.
5. Writer Agent가 어떤 순서로 설명하면 좋은지 제안하세요.


[중요]
최종 사용자용 문장을 화려하게 만드는 것보다 정확한 분석과 구조화가 중요합니다.

질문과 관련 없는 내용을 확장하지 마세요.

모르는 구체적인 사실을 만들지 마세요.

현재 질문은 교육용 AI/LLM 수업 문맥입니다.
"""

def research_agent_node(
        state: MultiAgentState
):

    print('\n')
    print('='*80)
    print('[Reseach Agent 실행]')
    print('='*80)

    question = state['question']
    audience = state['audience']

    print(f'Question : {question}')
    print(f'Audience : {audience}')

    result = research_model.invoke(
        [
            SystemMessage(
                content=RESEARCH_AGENT_PROMPT
            ),
            HumanMessage(
                content=(
                    f"""
사용자 질문:

{question}


답변 대상 수준:

{audience}


Writer Agent가 최종 답변을 작성할 수 있도록 질문을 분석하고 필요한 정보를 구조화하세요.
"""
                )
            )
        ]
    )


    print(f'\n[Research Summary]:\n{result.summary}')
    print('\n[Key Concepts]:')
    for concept in result.key_concepts:
        print(f'- {concept}')

    print('\n[Findings]:')
    for finding in result.findings:
        print(f'- {finding}')


    print('\n[Caution Points]:')
    for caution in result.caution_points:
        print(f'- {caution}')


    return {
        'research_summary': result.summary,
        'key_concepts': result.key_concepts,
        'findings': result.findings,
        'caution_points': result.caution_points,
        'recommended_structure': result.recommended_structure,
        'execution_order': [
            *state.get('execution_order', []),
            'research_agent'
        ]
    }


# Writer Agent Prompt

WRITER_AGENT_PROMPT = """
당신은 Writer Agent입니다.

Research Agent가 이미 질문을 분석했습니다.

당신의 역할은 Research Agent의 조사 결과를 이용하여
사용자에게 실제로 보여줄 최종 답변을 작성하는 것입니다.


==================================================================
[중요]
==================================================================

Research Agent의 Findings와 Caution Points를 무시하지 마세요.

Research Agent가 제공하지 않은 구체적인 사실을 임의로 추가하시 마세요.

질문의 핵심에 직접 답하세요.

사용자의 수준에 맞게 난이도를 조절하세요.


==================================================================
[답변 대상]
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
[출력]
==================================================================

자연스러운 한국어 설명을 작성하세요.

필요하면 간단한 코드 또는 흐름도를 텍스트 형태로 포함할 수 있습니다.
"""


def writer_agent_node(
        state: MultiAgentState
):
    print('\n')
    print('='*80)
    print('[Writer Agent 실행]')
    print('='*80)


    question = state['question']
    audience = state['audience']
    research_summary = state['research_summary']
    key_concepts = state['key_concepts']
    findings = state['findings']
    caution_points = state['caution_points']
    recommended_structure = state['recommended_structure']

    research_package = {
        'summary': research_summary,
        'key_concepts': key_concepts,
        'findings': findings,
        'caution_points': caution_points,
        'recommended_structure': recommended_structure
    }

    print('\n[Research Package Received]')
    print(
        json.dumps(
            research_package,
            ensure_ascii=False,
            indent=2
        )
    )


    response = model.invoke(
        [
            SystemMessage(
                content=WRITER_AGENT_PROMPT
            ),
            HumanMessage(
                content=f"""
사용자의 원래 질문:

{question}


답변 대상 수준:

{audience}


Research Agent가 전달한 조사 결과:

{
    json.dumps(
        research_package,
        ensure_ascii=False,
        indent=2
    )
}


위 조사 결과를 기반으로 사용자에게 보여줄 최종 답변을 작성하세요.
"""
            )
        ]
    )

    text = getattr(response, 'text', None)

    if not isinstance(text, str) and text:
        text = str(response.content)

    print('\n[Writer Result]')
    print(text)

    return {
        'final_answer': text,
        'execution_order': [
            *state.get('execution_order', []),
            'writer_agent'
        ]
    }


builder = StateGraph(MultiAgentState)

builder.add_node(
    'research_agent',
    research_agent_node
)

builder.add_node(
    'writer_agent',
    writer_agent_node
)

builder.add_edge(
    START,
    'research_agent'
)

builder.add_edge(
    'research_agent',
    'writer_agent'
)

builder.add_edge(
    'writer_agent',
    END
)

multi_agent_graph = builder.compile()


def run_multi_agent(
        question: str,
        audience: str,
        expected_focus: str
):

    print('\n\n')
    print('='*80)
    print('[Multi Agent Ex1]')
    print('='*80)

    print(f'\nquestion: {question}')
    print(f'\naudience: {audience}')
    print(f'\nexpected_focus: {expected_focus}')

    initial_state = {
        'question': question,
        'audience': audience,
        'research_summary': '',
        'key_concepts': [],
        'findings': [],
        'caution_points': [],
        'recommended_structure': [],
        'final_answer': '',
        'execution_order': []
    }


    result = multi_agent_graph.invoke(
        initial_state
    )

    print('\n')
    print('#'*80)
    print('Execution Summary')
    print('#'*80)

    print('\nExecution Order:')
    print(' -> '.join(result['execution_order']))

    print(f'\nResearch Concept Count:{len(result["key_concepts"])}')
    print(f'\nResearch Finding Count:{len(result["findings"])}')
    print(f'\nCaution Point Count:{len(result["caution_points"])}')

    print('\n\n')
    print('='*80)
    print('[Final Answer]')
    print('='*80)

    print(result['final_answer'])

    return result


TEST_CASES = [
    {
        'name': 'Beginner RAG',
        'question': 'RAG가 무엇인지 AI를 처음 배우는 학생도 이해할 수 있도록 설명해줘.',
        'audience': 'beginner',
        'expected': '검색 -> 근거 제공 -> 답변이라는 RAG의 기본 흐름을 쉽게 설명'
    }
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

            run_multi_agent(
                question=test['question'],
                audience=test['audience'],
                expected_focus=test['expected']
            )

    else:

        test = TEST_CASES[DEFAULT_EXAMPLE_INDEX]
        print(test['name'], end='\n\n')
        
        run_multi_agent(
            question=test['question'],
            audience=test['audience'],
            expected_focus=test['expected']
        )
