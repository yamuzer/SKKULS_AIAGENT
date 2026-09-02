import os
from dotenv import load_dotenv
from pathlib import Path
from google import genai
from typing import TypedDict
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

MODEL_NAME = 'gemini-3.6-flash'


class GraphState(TypedDict):
    question: str
    difficulty: str
    prompt: str
    answer: str


def make_prompt(state: GraphState):
    print('\n[make_prompt 실행]')
    question = state['question']
    difficulty = state['difficulty']
    print(f'질문: {question}')
    print(f'\n설명 수준: {difficulty}')

    prompt = f"""
다음 질문에 답해주세요.

질문:
{question}

설명 수준:
{difficulty}

조건:
- 설명 수준에 맞게 설명해주세요.
- 핵심 개념부터 설명해주세요.
- 너무 불필요하게 길게 설명하지 마세요.
- 필요한 경우 간단한 예제를 포함해주세요.
"""


    print(f'\n생성된 prompt:\n{prompt}')

    return {
        'prompt': prompt
    }


def gemini_node(state: GraphState):
    print('/n[gemini node 실행]')

    prompt = state['prompt']

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    answer = response.text
    print(f'\nGemini 응답:\n{answer}')

    return {
        'answer' : answer
    }


builder = StateGraph(GraphState)

builder.add_node(
    'make_prompt',
    make_prompt
)

builder.add_node(
    'gemini',
    gemini_node
)



builder.add_edge(
    START,
    'make_prompt'
)

builder.add_edge(
    'make_prompt',
    'gemini'
)

builder.add_edge(
    'gemini',
    END
)


graph = builder.compile()

initial_state = {
    'question': 'Transformer의 attention이 무엇인가요?',
    'difficulty': 'AI를 처음 배우는 초보자',
    'prompt': '',
    'answer': ''
}

result = graph.invoke(initial_state)

print('\n최종 state')
print(result)

print('\n최종답변:')
print(result['answer'])