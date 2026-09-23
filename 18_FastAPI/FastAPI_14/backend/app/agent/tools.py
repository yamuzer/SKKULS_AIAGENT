from langchain_core.tools import tool

@tool
def add_numbers(
    a: float,
    b: float
) -> str:
    '''
    두 숫자를 더해야 할 때 사용하는 도구입니다.
    '''

    result = a + b

    return f'{a} + {b} = {result}'


@tool
def multiply_numbers(
    a: float,
    b: float
) -> str:
    '''
    두 숫자를 곱해야 할 때 사용하는 도구입니다.
    '''

    result = a * b

    return f'{a} * {b} = {result}'


@tool
def get_course_info(
    topic: str
) -> str:
    '''
    FastAPI, React, LangGraph 수업 정보를 조회합니다.
    '''

    normalized = topic.strip().lower()

    course_data = {
        'fastapi':(
            'FastAPI 수업에서는 API, Pydantic, Router, Service, Depends, '
            'async/await, 파일 업로드, Streaming을 다룹니다.'
        ),

        'react': (
            'React 수업에서는 JSX, useState, 이벤트, fetch, 조건부 렌더링, '
            'Chat UI, FastAPI 연동을 중심으로 다룹니다.'
        ),

        'langgraph': (
            'LangGraph 수업에서는 State, Node, Edge, 조건 분기, ToolNode, '
            'Memory, Agent Workflow, Streaming을 다룹니다.'
        )
    }

    for key, value in course_data.items():
        if key in normalized:
            return value

    return '조회 가능한 주제는 FastAPI, React, LangGraph입니다.'


TOOLS = [
    add_numbers,
    multiply_numbers,
    get_course_info
]

