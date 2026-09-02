import os
from dotenv import load_dotenv
from pathlib import Path
from google import genai
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"

load_dotenv(dotenv_path=ENV_PATH)
api_key = os.getenv(
    "GEMINI_API_KEY"
)
if not api_key:
    raise ValueError('GEMINI_API_KEY를 읽을 수 없습니다.')

client = genai.Client(
    api_key=api_key
)

MODEL_NAME = 'gemini-3.7-flash'


class QuestionRoute(BaseModel):

    category: Literal[
        'python',
        'ai',
        'general'
    ] = Field(
        description='질문의 종류. Python 관련이면 python, AI/LLM 관련이면 ai, 그 외는 general'
    )

    reason: str = Field(
        description='해당 category로 분류한 이유'
    )


class GraphState(TypedDict):

    question: str
    category: str
    reason: str
    answer: str


def analyze_question(state: GraphState):

    print('\n[analyze_question 실행]')

    question = state['question']

    print(f'\n사용자 질문: \n{question}')

    prompt = f"""
다음 사용자 질문을 분류하세요.

질문:
{question}

분류 기준:

python
- Python 문법
- 리스트
- 딕셔너리
- 함수
- 클래스
- 패키지
- Python 코드


ai
- AI
- 머신러닝
- 딥러닝
- LLM
- Transformer
- LangChain
- LangGraph
- RAG
- VectorDB


general
- 위 두 범주에 해당하지 않는 일반적인 질문

반드시 질문의 핵심 주제를 기준으로 판단하세요.
"""

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
        response_format={
            'type':'text',
            'mime_type': 'application/json',
            'schema': QuestionRoute.model_json_schema()
        }
    )

    analysis = QuestionRoute.model_validate_json(
        interaction.output_text
    )

    print('\nGemini 분류 결과:')
    print(analysis.model_dump())

    return {
        'category': analysis.category,
        'reason': analysis.reason
    }


def route_question(state: GraphState):

    print('\n[route_question 실행]')

    category = state['category']
    print(f'선택된 category: {category}')

    return category


def python_node(state: GraphState):

    print('\n[python_node] 실행')

    question = state['question']

    prompt = f"""
다음 Python 질문에 답하세요.

질문:
{question}

조건:
- 초보자가 이해하기 쉽게 설명
- 핵심 개념을 먼저 설명
- 필요하면 간단한 코드 예제 포함
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return {
        'answer': response.text
    }



def ai_node(state: GraphState):

    print('\n[ai_node] 실행')

    question = state['question']

    prompt = f"""
다음 AI 관련 질문에 답하세요.

질문:
{question}

조건:
- 초보자가 이해하기 쉽게 설명
- 핵심 개념을 먼저 설명
- 필요하면 구조나 흐름을 단계적으로 설명
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return {
        'answer': response.text
    }



def general_node(state: GraphState):

    print('\n[general_node] 실행')

    question = state['question']

    prompt = f"""
다음 일반 질문에 답하세요.

질문:
{question}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return {
        'answer': response.text
    }


builder = StateGraph(GraphState)

builder.add_node(
    'analyze_question',
    analyze_question
)

builder.add_node(
    'python',
    python_node
)
builder.add_node(
    'ai',
    ai_node
)
builder.add_node(
    'general',
    general_node
)


builder.add_edge(
    START,
    'analyze_question'
)

builder.add_conditional_edges(
    'analyze_question',
    route_question,
    {
        'python': 'python',
        'ai': 'ai',
        'general': 'general'
    }
)

builder.add_edge(
    'python',
    END
)
builder.add_edge(
    'ai',
    END
)
builder.add_edge(
    'general',
    END
)


graph = builder.compile()

initial_state = {
    'question':'Python 리스트와 튜플의 차이를 알려줘.',
    'category': '',
    'reason': '',
    'answer': ''
}

result = graph.invoke(initial_state)

print('\ncategory:')
print(result['category'])

print('\nreason:')
print(result['reason'])

print('\n최종답변:')
print(result['answer'])