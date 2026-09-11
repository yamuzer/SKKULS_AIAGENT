import os
import chromadb
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.documents import Document
from langchain.messages import HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ENV_PATH = BASE_DIR / "../.env"
load_dotenv(dotenv_path=ENV_PATH)


GEMINI_API_KEY = os.getenv(
    'GEMINI_API_KEY'
)

GEMINI_MODEL = os.getenv(
    'GEMINI_MODEL',
    'gemini-3.7-flash'
)

GEMINI_EMBEDDING_MODEL = os.getenv(
    'GEMINI_EMBEDDING_MODEL',
    'gemini-embedding-2'
)

if not GEMINI_API_KEY:
    raise RuntimeError(
        'GEMINI_API_KEY가 없습니다.'
    )

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

CHROMA_DIR = DATA_DIR / "agent_vector_db"

COLLECTION_NAME = "agent_documents"

DATA_DIR.mkdir(
    parents=True, 
    exist_ok=True
)


DOCUMENTS = [

    Document(

        id="DOC-001",

        page_content=(
            "Python의 pandas는 표 형태의 데이터를 "
            "처리하고 분석하기 위한 라이브러리다. "
            "DataFrame을 이용해 필터링, 집계, "
            "결측치 처리 등을 수행할 수 있다."
        ),

        metadata={
            "doc_id": "DOC-001",
            "category": "data",
            "title": "Pandas 데이터 분석",
        },
    ),


    Document(

        id="DOC-002",

        page_content=(
            "NumPy는 다차원 배열과 수치 계산을 위한 "
            "Python 라이브러리다. 벡터화 연산을 통해 "
            "반복문보다 효율적인 수치 계산이 가능하다."
        ),

        metadata={
            "doc_id": "DOC-002",
            "category": "data",
            "title": "NumPy 수치 계산",
        },
    ),


    Document(

        id="DOC-003",

        page_content=(
            "Matplotlib은 Python의 대표적인 "
            "데이터 시각화 라이브러리다. "
            "선 그래프, 막대 그래프, 산점도 등 "
            "다양한 차트를 작성할 수 있다."
        ),

        metadata={
            "doc_id": "DOC-003",
            "category": "data",
            "title": "Matplotlib 시각화",
        },
    ),


    Document(

        id="DOC-004",

        page_content=(
            "머신러닝의 지도학습에서는 입력 데이터와 "
            "정답 Label을 이용해 모델을 학습한다. "
            "분류와 회귀가 대표적인 지도학습 문제다."
        ),

        metadata={
            "doc_id": "DOC-004",
            "category": "ai",
            "title": "지도학습 기초",
        },
    ),


    Document(

        id="DOC-005",

        page_content=(
            "Transformer는 Attention을 중심으로 "
            "Sequence 정보를 처리하는 모델 구조다. "
            "Self-Attention을 통해 Token 사이의 "
            "관계를 계산한다."
        ),

        metadata={
            "doc_id": "DOC-005",
            "category": "ai",
            "title": "Transformer 구조",
        },
    ),


    Document(

        id="DOC-006",

        page_content=(
            "RAG는 외부 문서를 검색한 뒤 검색 결과를 "
            "LLM의 Context로 제공하는 방식이다. "
            "모델의 내부 지식만 사용하는 것보다 "
            "외부 근거를 활용할 수 있다는 장점이 있다."
        ),

        metadata={
            "doc_id": "DOC-006",
            "category": "rag",
            "title": "RAG 기본 구조",
        },
    ),


    Document(

        id="DOC-007",

        page_content=(
            "Vector Database는 문서의 Embedding Vector를 "
            "저장하고 Query Vector와 가까운 문서를 "
            "검색하는 데 사용한다. ChromaDB는 이러한 "
            "Vector Search를 지원하는 데이터베이스다."
        ),

        metadata={
            "doc_id": "DOC-007",
            "category": "rag",
            "title": "Vector Database",
        },
    ),


    Document(

        id="DOC-008",

        page_content=(
            "Hybrid RAG는 Vector Search와 "
            "Knowledge Graph 검색처럼 서로 다른 "
            "검색 방법을 결합하여 Evidence를 "
            "수집하는 방식이다."
        ),

        metadata={
            "doc_id": "DOC-008",
            "category": "rag",
            "title": "Hybrid RAG",
        },
    ),


    Document(

        id="DOC-009",

        page_content=(
            "LangChain의 Tool은 LLM이 외부 기능을 "
            "사용할 수 있도록 Python 함수를 "
            "Tool 인터페이스로 변환한다. "
            "@tool decorator를 사용할 수 있다."
        ),

        metadata={
            "doc_id": "DOC-009",
            "category": "agent",
            "title": "LangChain Tool",
        },
    ),


    Document(

        id="DOC-010",

        page_content=(
            "LangGraph의 ToolNode는 AIMessage에 포함된 "
            "tool_calls를 읽어 등록된 Tool을 실행하고 "
            "실행 결과를 ToolMessage로 변환한다."
        ),

        metadata={
            "doc_id": "DOC-010",
            "category": "agent",
            "title": "LangGraph ToolNode",
        },
    ),


    Document(

        id="DOC-011",

        page_content=(
            "Agent Loop에서는 LLM이 Tool을 선택하고 "
            "Tool 실행 결과를 다시 관찰한 뒤 "
            "추가 Tool 호출이나 최종 답변을 결정한다."
        ),

        metadata={
            "doc_id": "DOC-011",
            "category": "agent",
            "title": "Agent Loop",
        },
    ),


    Document(

        id="DOC-012",

        page_content=(
            "Sequential Tool Calling은 첫 번째 Tool의 "
            "결과가 두 번째 Tool의 입력으로 필요한 "
            "경우에 사용된다. Agent는 Tool 결과를 "
            "확인한 뒤 다음 행동을 결정한다."
        ),

        metadata={
            "doc_id": "DOC-012",
            "category": "agent",
            "title": "Sequential Tool Calling",
        },
    ),


    Document(

        id="DOC-013",

        page_content=(
            "Knowledge Graph는 Entity와 Relation을 "
            "그래프 구조로 표현한다. NetworkX를 이용해 "
            "Node와 Edge를 구성하고 관계 탐색을 "
            "수행할 수 있다."
        ),

        metadata={
            "doc_id": "DOC-013",
            "category": "graph",
            "title": "Knowledge Graph",
        },
    ),


    Document(

        id="DOC-014",

        page_content=(
            "Graph RAG는 Knowledge Graph에서 "
            "Entity Relation을 탐색하여 관련 Evidence를 "
            "수집하고 이를 LLM 답변에 활용한다."
        ),

        metadata={
            "doc_id": "DOC-014",
            "category": "graph",
            "title": "Graph RAG",
        },
    ),


    Document(

        id="DOC-015",

        page_content=(
            "LangGraph의 MessagesState는 대화 과정의 "
            "HumanMessage, AIMessage, ToolMessage 등을 "
            "State에 누적하여 다음 Node가 이전 실행 "
            "결과를 사용할 수 있도록 한다."
        ),

        metadata={
            "doc_id": "DOC-015",
            "category": "agent",
            "title": "MessagesState",
        },
    ),


    Document(

        id="DOC-016",

        page_content=(
            "Agent의 Tool Description은 모델이 "
            "어떤 상황에서 어떤 Tool을 사용할지 "
            "판단하는 중요한 정보다. Tool의 목적, "
            "입력값, 사용 조건을 명확하게 작성해야 한다."
        ),

        metadata={
            "doc_id": "DOC-016",
            "category": "agent",
            "title": "Tool Description 설계",
        },
    ),


    Document(

        id="DOC-017",

        page_content=(
            "Pydantic args_schema를 사용하면 "
            "Agent Tool의 입력값에 타입, 기본값, "
            "범위와 선택 가능한 값을 지정하여 "
            "입력 검증을 수행할 수 있다."
        ),

        metadata={
            "doc_id": "DOC-017",
            "category": "agent",
            "title": "Tool args_schema",
        },
    ),


    Document(

        id="DOC-018",

        page_content=(
            "Corrective RAG는 검색 결과가 충분하지 않을 때 "
            "질문을 다시 작성하거나 검색 전략을 변경하여 "
            "더 적절한 Evidence를 찾는 접근 방법이다."
        ),

        metadata={
            "doc_id": "DOC-018",
            "category": "rag",
            "title": "Corrective RAG",
        },
    ),
]

embeddings = GoogleGenerativeAIEmbeddings(
    model=GEMINI_EMBEDDING_MODEL,
    output_dimensionality=768
)

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)

vector_store = Chroma(
    client=chroma_client,
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings
)


def initialize_vector_db():

    print('='*80)
    print('\nVector DB init')
    print('='*80)


    current_count = collection.count()
    print(f'현재 저장 문서 수: {current_count}')

    if current_count > 0:
        print('기존 ChromaDB를 사용합니다.')
        return

    print('문서를 embedding하여 저장합니다.')

    ids = [
        document.metadata['doc_id']
        for document in DOCUMENTS
    ]

    vector_store.add_documents(
        documents=DOCUMENTS,
        ids=ids
    )

    print(f'\n저장 완료: {collection.count()}')



class VectorSearchInput(BaseModel):

    query: str = Field(
        min_length=2,
        description=(
            '회사 내부 학습 문서에서 검색할 핵심 질문 또는 검색 주제'
        )
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=5,
        description='검색할 최대 문서 개수 1개 이상 5개 이하'
    )

    category: Literal[
        'all',
        'data',
        'ai',
        'rag',
        'agent',
        'graph'
    ] = Field(
        default='all',
        description=(
            '검색 범주. 전체 검색은 all,  데이터 분석은 data, AI는 ai, '
            'RAG는 rag, Agent는 agent, Knowledge Graph는 graph'
        )
    )


'''
vector search tool
'''

@tool
def vector_search(
    query: str,
    top_k: int = 3,
    category: str = 'all'
):
    '''
    회사 내부 교육 문서에서 의미적으로 관련된 문서를 검색한다.

    RAG, Agent, LangGraph, Knowledge Graph, 데이터 분석, AI 등의 
    내부 학습 자료를 찾아야 할 때 사용한다.

    일반 상식 질문에는 사용하지 않는다.

    사용자가 특정 카테고리를 지정했다면 category 값을 적절하게 설정한다.
    '''

    print('\n')
    print('='*80)
    print('[Tool Execution: vector_search]')
    print('='*80)


    print(f'query: {query}')
    print(f'top_k: {top_k}')
    print(f'category: {category}')


    filter_value = None

    if category != 'all':
        filter_value = {
            'category': category
        }

    if filter_value is None:
        search_results = vector_store.similarity_search_with_score(
            query,
            k=top_k
        )

    else:
        search_results = vector_store.similarity_search_with_score(
            query,
            k=top_k,
            filter=filter_value
        )


    results = []

    for rank, item in enumerate(search_results, start=1):

        document, score = item

        result = {
            'rank': rank,
            'doc_id': document.metadata.get('doc_id'),
            'title': document.metadata.get('title'),
            'category': document.metadata.get('category'),
            'content': document.page_content,
            'distance': float(score)
        }

        results.append(result)

    print(f'검색 결과 수: {len(results)}')

    return results



EMPLOYEE_DATA = {
    '철수': '데이터분석팀',
    '영희': 'AI개발팀',
    '민수': '서비스기획팀'
}

class EmployeeInput(BaseModel):

    employee_name: str = Field(
        description='부서를 확인할 직원 이름'
    )


@tool(args_schema=EmployeeInput)
def find_employee_department(
    employee_name: str
) -> dict:

    '''
    직원 이름으로 해당 직원의 소속 부서를 검색한다.

    직원 부서를 묻는 질문에만 사용한다.

    교육문서나 기술 자료를 검색하는 Tool이 아니다.
    '''

    print('\n')
    print('=' * 70)
    print('[Tool Execution: find_employee_department]')
    print('=' * 70)


    department = EMPLOYEE_DATA.get(employee_name)

    
    result = {
        'found': (
            department is not None
        ),
        'employee_name': employee_name,
        'department': department
    }


    print(f'result: {result}')

    return result


tools = [
    vector_search,
    find_employee_department
]

model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0,
    max_retries=2
)

model_wih_tools = model.bind_tools(tools)

SYSTEM_PROMPT = """
당신은 회사 내부 교육 자료와 직원 정보를 조회할 수 있는 Tool-Using Agent입니다.

다음 규칙을 반드시 지키세요.
1. 회사 내부 교육 문서의 내용에 대한 질문은 vector_search Tool을 사용하세요.
2. 직원 소속 부서를 묻는 질문은 find_employee_department Tool을 사용하세요.
3. Python 같은 일반 개념 질문에 대해 반드시 내부 문서가 필요한 것이 아니라면
   Tool을 사용하지 않고 직접 답변을 할 수 있습니다.
4. 사용자가 "사내 문서", "교육 자료", "내부 자료", "관련 문서" 등을 요구하면
   반드시 vector_search를 사용하세요.
5. 사용자가 문서 개수를 지정하면 top_k에 반영하세요.
6. 사용자가 Agent, RAG, Graph 등 명확한 분야를 지정하면 적절한 category를 사용하세요.
7. Tool 결과에 없는 내부 정보를 추측해서 만들지 마세요.
8. Vector Search 결과를 사용해 답변 할 때는 사용한 Document ID를 함께 표시하세요.
9. 필요한 정보를 얻은 뒤에는 불필요한 Tool을 다시 호출하지 마세요.
"""


class AgentState(MessagesState):

    tool_rounds: int

MAX_TOOL_ROUNDS = 4


def agent_node(
    state: AgentState
):

    print('='*70)
    print('[Agent Node 실행]')
    print('='*70)

    messages = state['messages']

    tool_rounds = state.get('tool_rounds', 0)

    print(f'message 수: {len(messages)}')
    print(f'tool round: {tool_rounds}')

    if tool_rounds >= MAX_TOOL_ROUNDS:
        print('\n최대 Tool Round에 도달했습니다.')

        return {
            'messages':[
                AIMessage(
                    content='도구 호출 횟수 제한에 도달하여 요청을 완료하지 못했습니다.'
                )
            ]
        }

    model_messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
        ),
        *messages
    ]

    response = model_wih_tools.invoke(model_messages)

    print('\n[Agent response]')
    print(response.content)

    print('\n[Tool Calls]')
    print(response.tool_calls)    

    if response.tool_calls:
        new_tool_rounds = tool_rounds + 1
        print(f'\nTool Round: {tool_rounds} -> {new_tool_rounds}')

        return {
            'messages':[
                response
            ],
            'tool_rounds': new_tool_rounds
        }

    print('\n추가 Tool Call 없음')
    print('-> 최종 답변')

    return {
        'messages': [
            response
        ]
    }

tool_node = ToolNode(tools)


def route_after_agent(
        state: AgentState
) -> Literal[
    'tools',
    'end'
]:

    print('='*70)
    print('[Router 실행]')
    print('='*70)


    last_message = state['messages'][-1]

    tool_calls = getattr(
        last_message,
        'tool_calls',
        []
    )

    if tool_calls:
        print(f'Tool call: {len(tool_calls)}')
        print('-> ToolNode')

        return 'tools'

    print(f'Tool call 없음')
    print('-> END')

    return 'end'



builder = StateGraph(AgentState)

builder.add_node(
    'agent',
    agent_node
)

builder.add_node(
    'tools',
    tool_node
)



builder.add_edge(
    START,
    'agent'
)

builder.add_conditional_edges(
    'agent',
    route_after_agent,
    {
        'tools': 'tools',
        'end': END
    }
)

builder.add_edge(
    'tools',
    'agent'
)


agent_graph = builder.compile()


def print_message(
        index,
        message
):

    print()
    print('='*70)
    print(f'Message {index}')
    print('='*70)

    if isinstance(message, HumanMessage):
        print('type: HumanMessage')
        print(message.content)

    elif isinstance(message, ToolMessage):
        print('type: ToolMessage')
        print(f'Tool: {message.name}')
        print(f'Tool Call ID: {message.tool_call_id}')
        print(message.content)

    elif isinstance(message, AIMessage):
        print('type: AIMessage')

        if message.tool_calls:
            print('\n[Tool Calls]')

            for tool_call in message.tool_calls:
                print(f'\nname: {tool_call.get("name")}')
                print(f'args: {tool_call.get("args")}')
                print(f'id: {tool_call.get("id")}')
    else:
        text = getattr(
            message,
            'text',
            None
        )

        if isinstance(text, str) and text:
            print()
            print(text)

        else:
            print(message.content)


def run_agent(
        question: str
):

    print('\n')
    print('#'*80)
    print('vector rag tool agent')
    print('#'*80)

    print('\n[사용자 질문]')
    print(question)

    initial_state = {
        'messages': [
            HumanMessage(
                content=question
            )
        ],
        'tool_rounds': 0,
    }

    result = agent_graph.invoke(
        initial_state,
        config={
            'recursion_limit': 15
        }
    )


    print('\n')
    print('#'*80)
    print('execution history')
    print('#'*80)

    print(f'총 Message 수: {len(result["messages"])}')
    print(f'총 Tool Round: {result.get("tool_rounds", 0)}')

    for index, message in enumerate(result['messages'], start=1):
        print_message(
            index,
            message
        )


    final_answer = result["messages"][-1]

    final_text = getattr(
        final_answer,
        'text',
        None
    )

    print('\n')
    print('='*80)
    print('Final Answer')
    print('='*80)

    if isinstance(final_text, str) and final_text:
        print(final_text)
    else:
        print(final_answer.content)

    return result


RUN_ALL_EXAMPLES = False

TEST_QUESTION = [
    (
        '사내 교육 자료에서 Agent Loop에 관한 문서를 찾아서 설명해줘.'
    ),
    (
        'RAG와 관련된 내부 문서를 2개 찾아서 핵심 내용을 정리해줘.'
    ),
    (
        'Agent 카테고리에서 ToolNode와 Tool Calling 관련 자료를 최대 3개 찾아줘'
    ),
    (
        '철수는 어는 부서에서 근무해?'
    ),
    (
        'Python의 for문이 무엇인지 아주 간단히 설명해줘.'
    )
]


initialize_vector_db()

if RUN_ALL_EXAMPLES:
    for index, question in enumerate(TEST_QUESTION, start=1):
        print('\n\n')
        print('='*80)
        print(f'Example {index}')
        print('='*80)

        run_agent(question)

else:
    run_agent(TEST_QUESTION[0])
