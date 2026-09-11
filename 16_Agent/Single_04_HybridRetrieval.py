import os
import chromadb
import networkx as nx
import json

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

CHROMA_DIR = DATA_DIR / "agent_multi_retrieval_db"

GRAPH_JSON_DIR = DATA_DIR / "agent_multi_retrieval_graph.json"

COLLECTION_NAME = "agent_multi_retrieval_documents"

DATA_DIR.mkdir(
    parents=True, 
    exist_ok=True
)


GRAPH_DATA = {

    "nodes": [

        # ----------------------------------------------------
        # Person
        # ----------------------------------------------------

        {
            "id": "철수",
            "type": "person",
        },

        {
            "id": "영희",
            "type": "person",
        },

        {
            "id": "민수",
            "type": "person",
        },

        {
            "id": "김현우",
            "type": "person",
        },

        {
            "id": "박서연",
            "type": "person",
        },


        # ----------------------------------------------------
        # Company
        # ----------------------------------------------------

        {
            "id": "ABC회사",
            "type": "company",
        },

        {
            "id": "XYZ연구소",
            "type": "company",
        },


        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        {
            "id": "서울",
            "type": "location",
        },

        {
            "id": "부산",
            "type": "location",
        },


        # ----------------------------------------------------
        # Department
        # ----------------------------------------------------

        {
            "id": "데이터분석팀",
            "type": "department",
        },

        {
            "id": "AI개발팀",
            "type": "department",
        },

        {
            "id": "서비스기획팀",
            "type": "department",
        },


        # ----------------------------------------------------
        # Project
        # ----------------------------------------------------

        {
            "id": "RAG프로젝트",
            "type": "project",
        },

        {
            "id": "Agent플랫폼",
            "type": "project",
        },

        {
            "id": "고객분석프로젝트",
            "type": "project",
        },


        # ----------------------------------------------------
        # Technology
        # ----------------------------------------------------

        {
            "id": "ChromaDB",
            "type": "technology",
        },

        {
            "id": "LangGraph",
            "type": "technology",
        },

        {
            "id": "Pandas",
            "type": "technology",
        },
    ],


    "relations": [

        # ----------------------------------------------------
        # 직원 → 회사
        # ----------------------------------------------------

        {
            "source": "철수",
            "target": "ABC회사",
            "relation": "works_at",
        },

        {
            "source": "영희",
            "target": "ABC회사",
            "relation": "works_at",
        },

        {
            "source": "민수",
            "target": "XYZ연구소",
            "relation": "works_at",
        },


        # ----------------------------------------------------
        # 회사 → 위치
        # ----------------------------------------------------

        {
            "source": "ABC회사",
            "target": "서울",
            "relation": "located_in",
        },

        {
            "source": "XYZ연구소",
            "target": "부산",
            "relation": "located_in",
        },


        # ----------------------------------------------------
        # 직원 → 부서
        # ----------------------------------------------------

        {
            "source": "철수",
            "target": "데이터분석팀",
            "relation": "belongs_to",
        },

        {
            "source": "영희",
            "target": "AI개발팀",
            "relation": "belongs_to",
        },

        {
            "source": "민수",
            "target": "서비스기획팀",
            "relation": "belongs_to",
        },


        # ----------------------------------------------------
        # 부서 → 팀장
        # ----------------------------------------------------

        {
            "source": "데이터분석팀",
            "target": "김현우",
            "relation": "managed_by",
        },

        {
            "source": "AI개발팀",
            "target": "박서연",
            "relation": "managed_by",
        },


        # ----------------------------------------------------
        # 부서 → 프로젝트
        # ----------------------------------------------------

        {
            "source": "데이터분석팀",
            "target": "RAG프로젝트",
            "relation": "runs",
        },

        {
            "source": "AI개발팀",
            "target": "Agent플랫폼",
            "relation": "runs",
        },

        {
            "source": "서비스기획팀",
            "target": "고객분석프로젝트",
            "relation": "runs",
        },


        # ----------------------------------------------------
        # 프로젝트 → 기술
        # ----------------------------------------------------

        {
            "source": "RAG프로젝트",
            "target": "ChromaDB",
            "relation": "uses",
        },

        {
            "source": "Agent플랫폼",
            "target": "LangGraph",
            "relation": "uses",
        },

        {
            "source": "고객분석프로젝트",
            "target": "Pandas",
            "relation": "uses",
        },
    ],
}




DOCUMENTS = [

    Document(

        page_content=(
            "ChromaDB는 Embedding Vector를 저장하고 "
            "유사도 검색을 수행할 수 있는 Vector Database다. "
            "RAG 시스템에서는 문서 Embedding을 저장하고 "
            "질문과 의미적으로 가까운 문서를 검색하는 데 "
            "사용할 수 있다."
        ),

        metadata={

            "doc_id":
                "DOC-001",

            "title":
                "ChromaDB 기본",

            "category":
                "rag",

            "technology":
                "ChromaDB",
        },
    ),


    Document(

        page_content=(
            "ChromaDB의 Metadata Filter를 이용하면 "
            "Vector Similarity Search와 함께 "
            "카테고리, 문서 종류 등의 조건으로 "
            "검색 대상을 제한할 수 있다."
        ),

        metadata={

            "doc_id":
                "DOC-002",

            "title":
                "ChromaDB Metadata Filter",

            "category":
                "rag",

            "technology":
                "ChromaDB",
        },
    ),


    Document(

        page_content=(
            "RAG는 질문과 관련된 외부 문서를 검색하고 "
            "검색된 Evidence를 LLM Context로 제공하여 "
            "답변을 생성하는 구조다."
        ),

        metadata={

            "doc_id":
                "DOC-003",

            "title":
                "RAG 기본 구조",

            "category":
                "rag",

            "technology":
                "general",
        },
    ),


    Document(

        page_content=(
            "Corrective RAG는 검색 Evidence가 부족하거나 "
            "질문과 관련성이 낮다고 판단될 때 "
            "Query를 다시 작성하고 재검색하는 구조다."
        ),

        metadata={

            "doc_id":
                "DOC-004",

            "title":
                "Corrective RAG",

            "category":
                "rag",

            "technology":
                "general",
        },
    ),


    Document(

        page_content=(
            "Hybrid RAG는 Vector Retrieval과 "
            "Knowledge Graph Retrieval처럼 서로 다른 "
            "검색 방법을 결합하여 Evidence를 수집한다."
        ),

        metadata={

            "doc_id":
                "DOC-005",

            "title":
                "Hybrid RAG",

            "category":
                "rag",

            "technology":
                "general",
        },
    ),


    Document(

        page_content=(
            "LangGraph는 LLM 애플리케이션의 실행 흐름을 "
            "State와 Node, Edge를 이용하여 구성할 수 있는 "
            "Workflow Framework다. 조건 분기와 반복 실행을 "
            "Graph 구조로 표현할 수 있다."
        ),

        metadata={

            "doc_id":
                "DOC-006",

            "title":
                "LangGraph 기본",

            "category":
                "agent",

            "technology":
                "LangGraph",
        },
    ),


    Document(

        page_content=(
            "LangGraph의 ToolNode는 AIMessage의 "
            "tool_calls를 읽어 등록된 Tool을 실행하고 "
            "Tool 실행 결과를 ToolMessage로 만들어 "
            "다음 Agent Node에 전달할 수 있다."
        ),

        metadata={

            "doc_id":
                "DOC-007",

            "title":
                "LangGraph ToolNode",

            "category":
                "agent",

            "technology":
                "LangGraph",
        },
    ),


    Document(

        page_content=(
            "Agent Loop에서는 LLM이 현재 Messages를 보고 "
            "Tool 호출 또는 최종 답변을 결정한다. "
            "Tool을 실행한 뒤 ToolMessage를 다시 관찰하고 "
            "추가 행동을 선택할 수 있다."
        ),

        metadata={

            "doc_id":
                "DOC-008",

            "title":
                "Agent Loop",

            "category":
                "agent",

            "technology":
                "general",
        },
    ),


    Document(

        page_content=(
            "Sequential Tool Calling에서는 첫 번째 Tool의 "
            "결과가 두 번째 Tool 호출에 필요한 입력값이 된다. "
            "따라서 첫 번째 Tool 결과를 관찰한 이후에 "
            "다음 Tool을 결정한다."
        ),

        metadata={

            "doc_id":
                "DOC-009",

            "title":
                "Sequential Tool Calling",

            "category":
                "agent",

            "technology":
                "general",
        },
    ),


    Document(

        page_content=(
            "Tool Description은 Agent가 여러 Tool 중 "
            "어떤 Tool을 선택할지 판단하는 데 사용되는 "
            "중요한 정보다. Tool의 목적과 사용 조건을 "
            "구체적으로 작성하는 것이 좋다."
        ),

        metadata={

            "doc_id":
                "DOC-010",

            "title":
                "Tool Description",

            "category":
                "agent",

            "technology":
                "general",
        },
    ),


    Document(

        page_content=(
            "Pandas는 표 형태의 데이터를 처리하기 위한 "
            "Python 데이터 분석 라이브러리다. "
            "DataFrame을 이용해 필터링, 집계, 결측치 처리와 "
            "데이터 변환 등을 수행할 수 있다."
        ),

        metadata={

            "doc_id":
                "DOC-011",

            "title":
                "Pandas 데이터 분석",

            "category":
                "data",

            "technology":
                "Pandas",
        },
    ),


    Document(

        page_content=(
            "Pandas의 groupby 기능을 사용하면 "
            "특정 열을 기준으로 데이터를 그룹화하고 "
            "평균, 합계, 개수 등의 집계 연산을 "
            "수행할 수 있다."
        ),

        metadata={

            "doc_id":
                "DOC-012",

            "title":
                "Pandas GroupBy",

            "category":
                "data",

            "technology":
                "Pandas",
        },
    ),


    Document(

        page_content=(
            "Knowledge Graph는 Entity와 Relation을 "
            "Node와 Edge 형태로 표현한다. "
            "명시적인 관계를 따라 Multi-Hop 탐색을 "
            "수행할 수 있다는 특징이 있다."
        ),

        metadata={

            "doc_id":
                "DOC-013",

            "title":
                "Knowledge Graph",

            "category":
                "graph",

            "technology":
                "general",
        },
    ),


    Document(

        page_content=(
            "Graph RAG에서는 Knowledge Graph의 Entity와 "
            "Relation을 탐색하여 질문에 필요한 관계 경로와 "
            "Evidence를 구성할 수 있다."
        ),

        metadata={

            "doc_id":
                "DOC-014",

            "title":
                "Graph RAG",

            "category":
                "graph",

            "technology":
                "general",
        },
    ),


    Document(

        page_content=(
            "Vector Search는 질문과 문서를 Embedding Vector로 "
            "변환한 뒤 Vector 공간에서 가까운 문서를 찾는다. "
            "정확한 Keyword가 일치하지 않아도 의미적으로 "
            "유사한 문서를 검색할 수 있다."
        ),

        metadata={

            "doc_id":
                "DOC-015",

            "title":
                "Vector Search",

            "category":
                "rag",

            "technology":
                "general",
        },
    ),


    Document(

        page_content=(
            "Graph Retrieval은 Entity Relation처럼 "
            "명시적인 구조적 관계 탐색에 적합하고, "
            "Vector Retrieval은 자연어 의미 유사성을 "
            "이용한 문서 검색에 적합하다."
        ),

        metadata={

            "doc_id":
                "DOC-016",

            "title":
                "Graph와 Vector Retrieval 비교",

            "category":
                "rag",

            "technology":
                "general",
        },
    ),
]


def save_graph_json():
    with open(
        GRAPH_JSON_DIR,
        'w',
        encoding='utf-8'
    ) as file:
        json.dump(
            GRAPH_DATA,
            file,
            ensure_ascii=False,
            indent=2
        )


def create_knowledge_graph():

    graph = nx.MultiDiGraph()

    for node in GRAPH_DATA['nodes']:
        graph.add_node(
            node['id'],
            type=node['type']
        )


    for relation in GRAPH_DATA['relations']:
        graph.add_edge(
            relation['source'],
            relation['target'],
            relation=relation['relation']
        )

    return graph


save_graph_json()

knowledge_graph = create_knowledge_graph()


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

    document_ids = [
        document.metadata['doc_id']
        for document in DOCUMENTS
    ]

    existing_result = collection.get(
        ids=document_ids
    )

    existing_ids = set(
        existing_result.get('ids', [])
    )

    current_count = collection.count()
    print(f'현재 저장 문서 수: {current_count}')

    missing_documents = []

    missing_ids = []

    for document in DOCUMENTS:
        doc_id = document.metadata['doc_id']

        if doc_id not in existing_ids:
            missing_documents.append(document)
            missing_ids.append(doc_id)

    if not missing_documents:
        print('Vector DB 초기화 완료')
        return

    print(f'추가할 문서 수: {len(missing_documents)}')


    vector_store.add_documents(
        documents=missing_documents,
        ids=missing_ids
    )

    print(f'\n저장 후 문서 수: {collection.count()}')


RelationType = Literal[
    'works_at',
    'located_in',
    'belongs_to',
    'managed_by',
    'runs',
    'uses',
]


class GraphSearchInput(BaseModel):

    start_entity: str = Field(
        min_length=1,
        description=(
            '관계 탐색을 시작할 정확한 Entity 이름. '
            '예: 철수, 영희, 민수, ABC 회사'
        )
    )


    relation_path: list[RelationType] = Field(
        min_length=1,
        max_length=4,
        description=(
            '시작할 Entity에서 순서대로 따라갈 관계. '
            'works_at=직원->회사, '
            'located_in=회사->위치, '
            'belongs_to=직원->부서, '
            'managed_by=부서->팀장, '
            'runs=부서->프로젝트, '
            'uses=프로젝트->기술, '
        )
    )



class VectorSearchInput(BaseModel):

    query: str = Field(
        min_length=2,
        description=(
            '내부 교육 문서에서 의미적으로 검색할 질문이나 핵심 주제'
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
            '검색 카데고리. '
            '전체는 all, '
            'RAG/VectorDB는 rag, '
            'Agent/LangGraph는 agent, '
            '데이터 분석은 data, '
            'Knowledge Graph는 graph'
        )
    )


def traverse_relation_path(
    start_entity: str,
    relation_path: list[str],
):

    # ========================================================
    # 시작 Entity 없음
    # ========================================================

    if (
        start_entity
        not in
        knowledge_graph
    ):

        return {

            "found":
                False,

            "start_entity":
                start_entity,

            "relation_path":
                relation_path,

            "reason":
                "Knowledge Graph에 시작 Entity가 없습니다.",

            "matches":
                [],
        }


    # ========================================================
    # 시작 Path
    # ========================================================

    paths = [

        {
            "current": start_entity,
            "steps": [],
        }
    ]


    # ========================================================
    # Relation 순차 탐색
    # ========================================================

    for relation_name in relation_path:

        next_paths = []


        for path in paths:

            current_node = path["current"]


            # =================================================
            # 현재 Node의 Outgoing Edge
            # =================================================

            for (
                source,
                target,
                key,
                edge_data,
            ) in knowledge_graph.out_edges(current_node, keys=True, data=True):

                edge_relation = edge_data.get(
                        "relation"
                )


                # =============================================
                # 원하는 관계가 아니면 Skip
                # =============================================

                if edge_relation != relation_name:

                    continue


                next_paths.append(
                    {
                        "current": target,

                        "steps": [
                            *path["steps"],
                            {
                                "source": source,
                                "relation": edge_relation,
                                "target": target
                            },
                        ],
                    }
                )


        # ====================================================
        # 관계를 더 따라갈 수 없음
        # ====================================================

        if not next_paths:

            return {
                "found": False,
                "start_entity": start_entity,
                "relation_path": relation_path,
                "reason": (
                    f"'{relation_name}' 관계를 "
                    "따라갈 수 없습니다."
                ),
                "matches": [],
            }


        paths = next_paths

    # ========================================================
    # 결과
    # ========================================================

    matches = []


    for path in paths:

        parts = [start_entity]


        for step in path["steps"]:
            parts.append(f"-[{step['relation']}]-> {step['target']}")


        matches.append(
            {

                "end_entity": path["current"],

                "end_entity_type":
                    knowledge_graph.nodes[path["current"]].get(
                        "type"
                    ),

                "path": path[ "steps"],

                "path_text": " ".join(parts),
            }
        )


    return {

        "found": True,

        "start_entity": start_entity,

        "relation_path": relation_path,

        "matches": matches,
    }


@tool(args_schema=GraphSearchInput)
def graph_search(
    start_entity: str,
    relation_path: list[str]
) -> dict:

    '''
    회사 Knowledge Graph에서 Entity 사이의
    명시적인 관계를 탐색한다.

    직원의 회사, 회사의 위치, 직원 부서, 부서 팀장, 부서 프로젝트,
    프로젝트 사용 기술 등 구조적인 관계 질문에 사용한다.

    Multi-Hop 관계 탐색이 가능하다.

    교육 문서의 개념 설명이나 의미 기반 검색에는 사용하지 않는다.
    '''
    print('\n')
    print('='*80)
    print('[Tool Execution: graph_search]')
    print('='*80)

    print(f'start_entity: {start_entity}')
    print(f'relation_path: {relation_path}')

    result = traverse_relation_path(
        start_entity=start_entity,
        relation_path=relation_path
    )

    print('[Graph Result]')
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )

    return result



@tool
def vector_search(
    query: str,
    top_k: int = 3,
    category: str = 'all'
):
    '''
    회사 내부 교육 문서에서 질문과 의미적으로 관련된
    자료를 Vector Search로 검색한다.

    RAG, ChromaDB, Agent, LangGraph, Pandas, Knowledge Graph 등의 개념 
    설명이나 관련 내부 자료를 찾을 때 사용한다.

    직원과 회사 사이의 명시적인 관계 탐색에는
    graph_search를 사용하고 이 Tool은 사용하지 않는다.
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
            'technology': document.metadata.get('technology'),
            'content': document.page_content,
            'distance': float(score)
        }

        results.append(result)

    print(f'검색 결과 수: {len(results)}')

    return results


tools = [
    graph_search,
    vector_search
]

model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0,
    max_retries=2
)

model_wih_tools = model.bind_tools(tools)

SYSTEM_PROMPT = """
당신은 두 가지 검색 Tool을 사용할 수 있는 회사 내부 정보 검색 Agent입니다.

사용 가능한 Tool은:

1. graph_search
2. vector_search


[graph_search]

Knowledge Graph의 명시적인 Entity Relation을 탐색할 때 사용합니다.

예:
철수가 근무하는 회사는?
-> graph_search
-> ["works_at"]

철수가 근무하는 회사 위치는?
-> graph_search
-> ["works_at", "located_in"]

철수가 속한 부서의 팀장은?
-> graph_search
-> ["belongs_to", "managed_by"]

철수가 속한 부서의 프로젝트가 사용하는 기술은?
-> graph_search
-> ["belongs_to", "runs", " uses"]

사용 가능한 관계:
works_at
직원 -> 회사

located_in
회사 -> 위치

belongs_to
직원 -> 부서

managed_by
부서 -> 팀장

runs
부서 -> 프로젝트

uses
프로젝트 -> 기술



[vector_search]
내부 교육 문서에서 자연어 의미를 기반으로 관련 자료를 검색할 때 사용합니다.

예:
RAG에 대한 내부 자료를 찾아줘.
-> vector_search

검색 결과가 부족할 때 다시 검색하는 방법에 대한 내부 교육 문서를 찾아줘.
->vector_search



[Graph + Vector]
사용자 질문에:

1. Entity 관계를 먼저 알아내야 하고
2. 그 관계 검색 결과로 얻은 Entity에 대한 교육 자료까지 찾아야 한다면

graph_search를 먼저 실행하세요.

그 결과를 확인 한 뒤 vector_seach를 실행하세요.

중요:
vector_search의 검색어가 graph_search 검색에 의존한다면 두 Tool을 동시에 
호출하지 마세요.

반드시:
graph_search
-> 결과 관찰
-> vector_search

순서대로 실행하세요.

예:

질문:
철수가 속한 부서의 프로젝트가 사용하는 기술을 찾고 그 기술에 대한 내부
자료도 설명해줘.

1단계:
graph_search

start_entity: 철수

relation_path:
[
    "belongs_to",
    "runs",
    "uses"
]

결과:
ChromaDB

2단계:
vector_search

query: ChromaDB



[기타 규칙]
1. 회사 내부 관계를 추측하지 마세요.
2. 내부 교육 문서를 요구하면 vector_search를 사용하세요.
3. Graph 결과가 필요한 Vector Search에서는 반드시 Graph 결과를 먼저 확인하세요.
4. 검색 결과가 이미 충분하다면 같은 Tool을 반복 호출하지 마세요.
5. Tool 결과에 없는 내부 정보를 만들어내지 마세요.
6. Vector Search 결과를 사용한 답변에는 참고한 Documnet ID를 표시하세요.
7. 일반적인 Python 문법처럼 내부 자료가 필요하지 않은 질문은 
   Tool 없이 직접 답할 수 있습니다.
"""


class AgentState(MessagesState):

    tool_rounds: int

MAX_TOOL_ROUNDS = 6


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


def extract_tool_sequence(
        messages
):

    sequence = []

    for message in messages:
        if not isinstance(message, AIMessage):
            continue

        for tool_call in message.tool_calls:
            sequence.append(
                tool_call.get('name')
            )

    return sequence


def run_agent(
        question: str,
        expected_flow: str | None = None
):

    print('\n')
    print('#'*80)
    print('graph + vector use agent')
    print('#'*80)

    print('\n[사용자 질문]')
    print(question)


    if expected_flow is not None:
        print('[Expected Flow]') 
        print(expected_flow)


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
            'recursion_limit': 20
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


    actual_sequence = extract_tool_sequence(
        result['messages']
    )

    print('\n')
    print('='*80)
    print('Tool Sequence')
    print('='*80)

    if actual_sequence: 
        print(f' -> '.join(actual_sequence))

    else:
        print('Tool 사용 안 함')


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






TEST_CASES = [
    # Graph 1-hop
    {
        'question': '철수가 근무하는 회사가 어디야?',
        'expected_flow': 'graph_search'
    },

    # Graph 2-hop
    {
        'question': '철수가 근무하는 회사는 어느 지역에 있어?',
        'expected_flow': 'graph_search'
    },

    # Graph 3-hop
    {
        'question': '철수가 속한 부서에서 진행하는 프로젝트가 사용하는 기술은 뭐야?',
        'expected_flow': 'graph_search'
    },

    # Vector Search
    {
        'question': '사내 교육 자료에서 Agent Loop에 대한 내용을 찾아서 설명해줘.',
        'expected_flow': 'vector_search'
    },

    # Vector Semantic Search 
    {
        'question': '내부 교육 자료 중에서 검색 결과가 부족할 때 질문을 다시 바꾸고 재검색하는 방법에 대한 자료를 찾아줘.',
        'expected_flow': 'vector_search'
    },

    # graph -> vector
    {
        'question': (
            '철수가 속한 부서에서 진행하는 프로젝트가 사용하는 기술을 먼저 찾아줘. '
            '그리고 그 기술에 대한 내부 교육 자료도 찾아서 설명해줘'
        ),
        'expected_flow': 'graph_search -> vector_search'
    },

    # Tool 불필요
    {
        'question': (
            'Python의 list와 tuple 차이를 간단히 설명해줘'
        ),
        'expected_flow': 'Tool 사용 안 함'
    },
]

RUN_ALL_EXAMPLES = True

initialize_vector_db()

if RUN_ALL_EXAMPLES:
    for index, test_case in enumerate(TEST_CASES, start=1):
        print('\n\n')
        print('='*80)
        print(f'Example {index}')
        print('='*80)

        run_agent(
            question=test_case['question'],
            expected_flow=test_case['expected_flow']    
        )

else:
    run_agent(
        question=TEST_CASES[1]['question'],
        expected_flow=TEST_CASES[1]['expected_flow']
        )
