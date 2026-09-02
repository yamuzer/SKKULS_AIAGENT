from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class GraphState(TypedDict):

    question: str

    category: str

    answer: str


def classify_question(state: GraphState):
    print('\n[classify_question 실행]')

    question = state['question']

    print(f'질문: {question}')

    question_lower = question.lower()

    if (
        'python' in question_lower
         or '파이썬' in question_lower
         or '리스트' in question_lower
         or '딕셔너리' in question_lower
    ):
        category = 'python'
    elif (
        'llm' in question_lower
            or 'ai' in question_lower
            or '인공지능' in question_lower
            or 'langchain' in question_lower
            or 'langgraph' in question_lower
    ):
        category = 'ai'
    else:
        category = 'general'

    print(f'분류 결과: {category}')

    return {
        'category': category
    }


def python_node(state: GraphState):
    print('\n[python_node 실행]')

    question = state['question']

    answer = f'Python 관련 질문입니다. 입력된 질문: {question}'

    return {
        'answer': answer
    }


def ai_node(state: GraphState):
    print('\n[ai_node 실행]')

    question = state['question']

    answer = f'AI 관련 질문입니다. 입력된 질문: {question}'

    return {
        'answer': answer
    }


def general_node(state: GraphState):
    print('\n[general_node 실행]')

    question = state['question']

    answer = f'일반 질문입니다. 입력된 질문: {question}'

    return {
        'answer': answer
    }


def route_question(state: GraphState):

    category = state['category']

    print('\n[route_question 실행]')

    print(f'이동할 경로: {category}')

    return category


builder = StateGraph(GraphState)

builder.add_node(
    'classify_question',
    classify_question
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
    'classify_question'
)

builder.add_conditional_edges(
    'classify_question',
    route_question
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
    'question': '파이썬 리스트가 뭐야?',
    'category': '',
    'answer': ''
}

result = graph.invoke(initial_state)

print('\n최종 결과')
print(result)
print(f'\n최종 답변: {result['answer']}')