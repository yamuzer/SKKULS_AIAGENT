import json
import os
from collections import deque
from pathlib import Path
from typing import Literal, TypedDict

import chromadb
import networkx as nx
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph


# ============================================================
# 1. 환경 설정
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"

load_dotenv(dotenv_path=ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY가 없습니다. .env 파일을 확인하세요."
    )

DATA_DIR = BASE_DIR / "data"
GRAPH_PATH = DATA_DIR / "knowledge_graph.json"
CHROMA_DIR = DATA_DIR / "chroma_db"

GRAPH_MAX_HOPS = 3
VECTOR_TOP_K = 5
VECTOR_FETCH_K = 10


# ============================================================
# 2. Knowledge Graph 로드
#    prepare_data.py가 만든 knowledge_graph.json 재사용
# ============================================================

if not GRAPH_PATH.exists():
    raise FileNotFoundError(
        "knowledge_graph.json이 없습니다. "
        "먼저 prepare_data.py를 실행하세요."
    )

with open(
    GRAPH_PATH,
    "r",
    encoding="utf-8",
) as file:
    graph_data = json.load(file)


graph = nx.MultiDiGraph()

for node in graph_data["nodes"]:
    graph.add_node(
        node["id"],
        type=node.get(
            "type",
            "Other",
        ),
        source_documents=node.get(
            "source_documents",
            [],
        ),
    )

for relation in graph_data["relations"]:
    graph.add_edge(
        relation["source"],
        relation["target"],
        key=relation["edge_id"],
        relation=relation["relation"],
        source_document=relation["source_document"],
    )


# ============================================================
# 3. ChromaDB 로드
#    build_vector_db.py가 만든 DB 재사용
# ============================================================

if not CHROMA_DIR.exists():
    raise FileNotFoundError(
        "ChromaDB가 없습니다. "
        "먼저 build_vector_db.py를 실행하세요."
    )

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

COLLECTION_NAME = "company_knowledge_documents"

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)

# VectorDB를 만들 때 사용한 Embedding 설정 복원
collection_metadata = collection.metadata or {}

EMBEDDING_MODEL = collection_metadata.get(
    "embedding_model",
    "gemini-embedding-2",
)

EMBEDDING_DIMENSION = int(
    collection_metadata.get(
        "embedding_dimension",
        768,
    )
)


# ============================================================
# 4. Gemini / LangChain 모델
# ============================================================

# Embedding은 기존 실습처럼 google-genai SDK 사용
gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)

# 질문 분석과 답변 생성은 LangChain Integration 사용
CHAT_MODEL = os.getenv(
    "GEMINI_CHAT_MODEL",
    "gemini-3.7-flash",
)

llm = ChatGoogleGenerativeAI(
    model=CHAT_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0,
)


# ============================================================
# 5. 사용 가능한 Knowledge Graph Relation
# ============================================================

RELATION_TYPES = [
    "WORKS_IN",
    "PARTICIPATES_IN",
    "USES",
    "BELONGS_TO",
    "LOCATED_IN",
]


# ============================================================
# 6. LangChain Structured Output Schema
#
# search_mode를 Gemini가 바로 정하게 하지 않는다.
# 대신:
#   needs_graph
#   needs_vector
# 를 각각 판단하게 하고 Python에서 search_mode를 만든다.
# ============================================================


class QuestionAnalysis(BaseModel):
    needs_graph: bool = Field(
        description=(
            "질문 해결에 Entity 사이의 명시적인 "
            "Knowledge Graph 관계 탐색이 필요한가"
        )
    )

    needs_vector: bool = Field(
        description=(
            "질문 해결에 문서 의미 기반 Vector Search가 필요한가"
        )
    )

    relation_types: list[
        Literal[
            "WORKS_IN",
            "PARTICIPATES_IN",
            "USES",
            "BELONGS_TO",
            "LOCATED_IN",
        ]
    ] = Field(
        default_factory=list,
        description="질문 해결에 필요한 Graph Relation 종류",
    )

    reason: str = Field(
        description="검색 방법을 선택한 이유"
    )


analysis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
너는 사내 Knowledge 검색 시스템의 Query Analyzer다.

Knowledge Graph Relation:
- WORKS_IN: 사람 -> 부서
- PARTICIPATES_IN: 사람 -> 프로젝트
- USES: 사람/프로젝트 -> 기술
- BELONGS_TO: 프로젝트 -> 부서
- LOCATED_IN: 부서 -> 지역

판단 규칙:

1. Entity 사이의 명확한 관계를 알아야 하면 needs_graph=true

예:
- 김철수가 참여하는 프로젝트는?
- VisionGuard에 참여하는 사람은?
- 윤도현이 참여하는 프로젝트가 속한 팀은 어디야?

2. 설명이나 의미적으로 비슷한 문서를 찾아야 하면 needs_vector=true

예:
- 제품 사진으로 불량을 찾는 프로젝트는?
- 문서를 검색해 답변하는 프로젝트를 설명해줘.

3. 두 종류의 정보가 모두 필요하면 둘 다 true

예:
- 김철수가 참여하는 프로젝트 중 이미지 불량 검사와 관련된 프로젝트를 설명해줘.

이 경우:
needs_graph=true
needs_vector=true
relation_types=["PARTICIPATES_IN"]

4. multi-hop 관계 질문이면 필요한 Relation을 모두 넣어라.

예:
윤도현이 참여하는 프로젝트가 속한 팀은 어디야?
-> PARTICIPATES_IN, BELONGS_TO, LOCATED_IN
""".strip(),
        ),
        (
            "human",
            "질문: {question}\n발견된 Graph Entity: {entities}",
        ),
    ]
)

structured_llm = llm.with_structured_output(
    schema=QuestionAnalysis.model_json_schema(),
    method="json_schema",
)

analysis_chain = analysis_prompt | structured_llm


# ============================================================
# 7. LangGraph State
# ============================================================


class SearchState(TypedDict, total=False):
    question: str

    entities: list[str]

    needs_graph: bool
    needs_vector: bool

    search_mode: Literal[
        "graph",
        "vector",
        "hybrid",
    ]

    relation_types: list[str]
    analysis_reason: str

    graph_results: list[dict]
    graph_candidate_projects: list[str]

    vector_results: list[dict]

    answer: str


# ============================================================
# 8. 질문에서 실제 Graph Entity 찾기
# ============================================================


def find_entities(
    question: str,
) -> list[str]:

    matched_entities = []

    entity_names = sorted(
        graph.nodes(),
        key=len,
        reverse=True,
    )

    for entity in entity_names:
        if entity in question:
            matched_entities.append(entity)

    return matched_entities


# ============================================================
# 9. 기존 실습 복습용 Relation Keyword Rule
#
# Gemini 판단만 믿지 않고 규칙으로 한번 보정한다.
# ============================================================


def infer_relation_types_rule(
    question: str,
) -> list[str]:

    relations = []

    # 사람 -> 프로젝트
    if (
        "참여" in question
        or "참여하는" in question
    ):
        relations.append(
            "PARTICIPATES_IN"
        )

    # 사람/프로젝트 -> 기술
    if (
        "기술" in question
        or "사용" in question
        or "도구" in question
    ):
        relations.append(
            "USES"
        )

    # 사람 -> 부서
    if (
        "근무" in question
        or "소속" in question
    ):
        relations.append(
            "WORKS_IN"
        )

    # 프로젝트 -> 부서
    if (
        "속한 팀" in question
        or "속한 부서" in question
        or "주관" in question
    ):
        relations.append(
            "BELONGS_TO"
        )

    # 부서 -> 위치
    if (
        "어디" in question
        or "위치" in question
        or "근무지" in question
    ):
        relations.append(
            "LOCATED_IN"
        )

    # 중복 제거
    result = []

    for relation in relations:
        if relation not in result:
            result.append(relation)

    return result


# ============================================================
# 10. Vector Search가 필요한 의미 표현 Rule
# ============================================================


def needs_vector_rule(
    question: str,
) -> bool:

    semantic_keywords = [
        "관련",
        "설명",
        "어떤",
        "무슨",
        "비슷",
        "내용",
        "찾는 프로젝트",
        "뭐야",
    ]

    return any(
        keyword in question
        for keyword in semantic_keywords
    )


# ============================================================
# 11. LangChain + Gemini 질문 분석 Node
# ============================================================


def analyze_question_node(
    state: SearchState,
) -> dict:

    question = state["question"]

    entities = find_entities(
        question
    )

    raw_analysis = analysis_chain.invoke(
        {
            "question": question,
            "entities": entities,
        }
    )

    analysis = QuestionAnalysis.model_validate(
        raw_analysis
    )

    # --------------------------------------------------------
    # 1) Keyword Relation Rule
    # --------------------------------------------------------

    rule_relations = infer_relation_types_rule(
        question
    )

    # LLM + Rule Relation 합치기
    relation_types = []

    for relation in (
        list(analysis.relation_types)
        + rule_relations
    ):
        if relation not in relation_types:
            relation_types.append(relation)

    # --------------------------------------------------------
    # 2) Graph 필요 여부 보정
    #
    # Graph Entity가 있고 관계 키워드까지 있으면
    # Gemini가 vector라고 했더라도 Graph가 필요하다.
    # --------------------------------------------------------

    needs_graph = analysis.needs_graph

    if entities and rule_relations:
        needs_graph = True

    # Entity가 없으면 지금 구현의 Graph Search는 시작점이 없다.
    if not entities:
        needs_graph = False

    # --------------------------------------------------------
    # 3) Vector 필요 여부 보정
    # --------------------------------------------------------

    needs_vector = analysis.needs_vector

    if needs_vector_rule(question):
        needs_vector = True

    # 둘 다 False가 되는 비정상 경우는 Vector로 fallback
    if not needs_graph and not needs_vector:
        needs_vector = True

    # --------------------------------------------------------
    # 4) 최종 Search Mode 결정
    # --------------------------------------------------------

    if needs_graph and needs_vector:
        search_mode = "hybrid"

    elif needs_graph:
        search_mode = "graph"

    else:
        search_mode = "vector"

    return {
        "entities": entities,
        "needs_graph": needs_graph,
        "needs_vector": needs_vector,
        "search_mode": search_mode,
        "relation_types": relation_types,
        "analysis_reason": analysis.reason,
    }


# ============================================================
# 12. Knowledge Graph BFS
#
# Relation Filter와 Graph Traversal을 분리한다.
#
# filter에 없는 Edge라도 다음 Node로는 이동한다.
# 그래야 multi-hop 검색이 끊기지 않는다.
# ============================================================


def bfs_graph_search(
    start_entities: list[str],
    relation_filters: list[str],
    max_hops: int = GRAPH_MAX_HOPS,
) -> list[dict]:

    if not start_entities:
        return []

    queue = deque(
        (
            entity,
            0,
        )
        for entity in start_entities
    )

    visited_nodes = set(
        start_entities
    )

    visited_edges = set()

    results = []

    while queue:

        current_node, hop = (
            queue.popleft()
        )

        if hop >= max_hops:
            continue

        edge_groups = [
            (
                "OUT",
                graph.out_edges(
                    current_node,
                    keys=True,
                    data=True,
                ),
            ),
            (
                "IN",
                graph.in_edges(
                    current_node,
                    keys=True,
                    data=True,
                ),
            ),
        ]

        for traversal, edges in edge_groups:

            for (
                source,
                target,
                edge_key,
                data,
            ) in edges:

                relation_name = data.get(
                    "relation",
                    "",
                )

                # --------------------------------------------
                # 결과 포함 여부
                # --------------------------------------------

                matches_filter = (
                    not relation_filters
                    or relation_name
                    in relation_filters
                )

                if (
                    matches_filter
                    and edge_key
                    not in visited_edges
                ):
                    results.append(
                        {
                            "edge_id": edge_key,
                            "source": source,
                            "relation": relation_name,
                            "target": target,
                            "source_document": data.get(
                                "source_document",
                                "",
                            ),
                            "hop": hop + 1,
                            "traversal": traversal,
                        }
                    )

                    visited_edges.add(
                        edge_key
                    )

                # --------------------------------------------
                # BFS Traversal
                # filter와 관계없이 다음 Node로 이동
                # --------------------------------------------

                if traversal == "OUT":
                    next_node = target
                else:
                    next_node = source

                if next_node not in visited_nodes:

                    visited_nodes.add(
                        next_node
                    )

                    queue.append(
                        (
                            next_node,
                            hop + 1,
                        )
                    )

    return results


# ============================================================
# 13. Graph에서 시작 Entity의 Project 후보 추출
#
# Hybrid 질문:
# 김철수가 참여하는 프로젝트 중 ...
#
# 여기서는 김철수 --PARTICIPATES_IN--> Project만 뽑아서
# Vector 결과를 우선순위화할 때 사용한다.
# ============================================================


def extract_candidate_projects(
    start_entities: list[str],
    graph_results: list[dict],
) -> list[str]:

    candidates = []

    for item in graph_results:

        if (
            item["relation"]
            != "PARTICIPATES_IN"
        ):
            continue

        if (
            item["source"]
            not in start_entities
        ):
            continue

        project_name = item["target"]

        if (
            graph.nodes[
                project_name
            ].get("type")
            != "Project"
        ):
            continue

        if project_name not in candidates:
            candidates.append(
                project_name
            )

    return candidates


# ============================================================
# 14. Graph Search Node
# ============================================================


def graph_search_node(
    state: SearchState,
) -> dict:

    results = bfs_graph_search(
        start_entities=state.get(
            "entities",
            [],
        ),
        relation_filters=state.get(
            "relation_types",
            [],
        ),
        max_hops=GRAPH_MAX_HOPS,
    )

    candidate_projects = (
        extract_candidate_projects(
            state.get(
                "entities",
                [],
            ),
            results,
        )
    )

    return {
        "graph_results": results,
        "graph_candidate_projects": (
            candidate_projects
        ),
    }


# ============================================================
# 15. Gemini Query Embedding
# ============================================================


def prepare_query_text(
    question: str,
) -> str:

    return (
        "task: search result | "
        f"query: {question}"
    )



def create_query_embedding(
    question: str,
) -> list[float]:

    query_text = prepare_query_text(
        question
    )

    result = (
        gemini_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query_text,
            config=(
                types.EmbedContentConfig(
                    output_dimensionality=(
                        EMBEDDING_DIMENSION
                    )
                )
            ),
        )
    )

    if not result.embeddings:
        raise RuntimeError(
            "Query Embedding 결과가 없습니다."
        )

    vector = list(
        result.embeddings[0].values
    )

    return vector


# ============================================================
# 16. ChromaDB Vector Search
# ============================================================


def vector_search(
    question: str,
    top_k: int = VECTOR_FETCH_K,
) -> list[dict]:

    query_embedding = (
        create_query_embedding(
            question
        )
    )

    search_result = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=min(
            top_k,
            collection.count(),
        ),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    ids = search_result["ids"][0]
    documents = (
        search_result["documents"][0]
    )
    metadatas = (
        search_result["metadatas"][0]
    )
    distances = (
        search_result["distances"][0]
    )

    results = []

    for index in range(
        len(ids)
    ):

        results.append(
            {
                "rank": index + 1,
                "doc_id": ids[index],
                "title": (
                    metadatas[index][
                        "title"
                    ]
                ),
                "category": (
                    metadatas[index][
                        "category"
                    ]
                ),
                "text": documents[index],
                "distance": distances[index],
            }
        )

    return results


# ============================================================
# 17. Hybrid용 Vector 결과 우선순위 조정
#
# Graph에서 얻은 프로젝트 후보가 있으면
# 그 프로젝트 이름이 포함된 Vector 문서를 먼저 배치한다.
#
# 예:
# Graph 후보 = VisionGuard, DocuMind
# Vector 검색 = 이미지 불량 관련 문서
# -> VisionGuard 문서를 우선
# ============================================================


def prioritize_vector_results(
    results: list[dict],
    candidate_projects: list[str],
    top_k: int = VECTOR_TOP_K,
) -> list[dict]:

    if not candidate_projects:
        return results[:top_k]

    candidate_results = []
    other_results = []

    for item in results:

        searchable_text = (
            f"{item['title']} "
            f"{item['text']}"
        )

        matched = any(
            project in searchable_text
            for project
            in candidate_projects
        )

        if matched:
            candidate_results.append(
                item
            )
        else:
            other_results.append(
                item
            )

    merged = (
        candidate_results
        + other_results
    )

    # rank를 다시 보기 좋게 부여
    final_results = []

    for index, item in enumerate(
        merged[:top_k],
        start=1,
    ):
        copied = dict(item)
        copied["rank"] = index
        final_results.append(copied)

    return final_results


# ============================================================
# 18. Vector Search Node
# ============================================================


def vector_search_node(
    state: SearchState,
) -> dict:

    raw_results = vector_search(
        state["question"],
        top_k=VECTOR_FETCH_K,
    )

    final_results = (
        prioritize_vector_results(
            raw_results,
            state.get(
                "graph_candidate_projects",
                [],
            ),
            top_k=VECTOR_TOP_K,
        )
    )

    return {
        "vector_results": final_results
    }


# ============================================================
# 19. Graph Context 문자열
# ============================================================


def format_graph_context(
    results: list[dict],
) -> str:

    if not results:
        return (
            "Knowledge Graph 검색 결과 없음"
        )

    lines = []

    for item in results:

        lines.append(
            (
                f"- {item['source']} "
                f"--{item['relation']}--> "
                f"{item['target']} "
                f"(hop={item['hop']}, "
                f"source={item['source_document']})"
            )
        )

    return "\n".join(lines)


# ============================================================
# 20. Vector Context 문자열
# ============================================================


def format_vector_context(
    results: list[dict],
) -> str:

    if not results:
        return "Vector 검색 결과 없음"

    blocks = []

    for item in results:

        blocks.append(
            (
                f"[{item['rank']}] "
                f"{item['title']}\n"
                f"category: "
                f"{item['category']}\n"
                f"document_id: "
                f"{item['doc_id']}\n"
                f"distance: "
                f"{item['distance']}\n"
                f"text: "
                f"{item['text']}"
            )
        )

    return "\n\n".join(blocks)


# ============================================================
# 21. LangChain 최종 Answer Chain
# ============================================================

answer_prompt = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
너는 사내 Knowledge QA Assistant다.
반드시 제공된 검색 결과를 근거로 답한다.

규칙:
1. Graph 결과는 Entity 사이의 명시적인 관계 근거다.
2. Graph Candidate Project는 Graph에서 직접 확인된 후보 프로젝트다.
3. Vector 결과는 의미적으로 관련 있는 문서 근거다.
4. hybrid 검색에서는 Graph Candidate Project 범위와 Vector 문서 의미를 함께 사용한다.
5. 근거에 없는 내용을 만들지 않는다.
6. multi-hop 관계이면 경로를 순서대로 설명한다.
7. 답변 마지막에는 근거를 간단히 구분한다.
   - Graph 근거
   - Vector 근거
""".strip(),
            ),
            (
                "human",
                """
질문:
{question}

검색 방식:
{search_mode}

Graph Candidate Project:
{candidate_projects}

Graph 검색 결과:
{graph_context}

Vector 검색 결과:
{vector_context}
""".strip(),
            ),
        ]
    )
)

answer_chain = answer_prompt | llm


# ============================================================
# 22. 최종 답변 Node
# ============================================================


def generate_answer_node(
    state: SearchState,
) -> dict:

    response = answer_chain.invoke(
        {
            "question": (
                state["question"]
            ),
            "search_mode": (
                state.get(
                    "search_mode",
                    "hybrid",
                )
            ),
            "candidate_projects": (
                state.get(
                    "graph_candidate_projects",
                    [],
                )
            ),
            "graph_context": (
                format_graph_context(
                    state.get(
                        "graph_results",
                        [],
                    )
                )
            ),
            "vector_context": (
                format_vector_context(
                    state.get(
                        "vector_results",
                        [],
                    )
                )
            ),
        }
    )

    answer_text = getattr(
        response,
        "text",
        None,
    )

    if not answer_text:
        answer_text = str(
            response.content
        )

    return {
        "answer": answer_text
    }


# ============================================================
# 23. LangGraph Router
# ============================================================


def route_after_analysis(
    state: SearchState,
) -> str:

    if state["search_mode"] == "vector":
        return "vector_search"

    # graph / hybrid
    return "graph_search"



def route_after_graph(
    state: SearchState,
) -> str:

    if state["search_mode"] == "hybrid":
        return "vector_search"

    return "generate_answer"


# ============================================================
# 24. LangGraph 구성
# ============================================================

builder = StateGraph(
    SearchState
)

builder.add_node(
    "analyze_question",
    analyze_question_node,
)

builder.add_node(
    "graph_search",
    graph_search_node,
)

builder.add_node(
    "vector_search",
    vector_search_node,
)

builder.add_node(
    "generate_answer",
    generate_answer_node,
)

builder.add_edge(
    START,
    "analyze_question",
)

builder.add_conditional_edges(
    "analyze_question",
    route_after_analysis,
    {
        "graph_search": (
            "graph_search"
        ),
        "vector_search": (
            "vector_search"
        ),
    },
)

builder.add_conditional_edges(
    "graph_search",
    route_after_graph,
    {
        "vector_search": (
            "vector_search"
        ),
        "generate_answer": (
            "generate_answer"
        ),
    },
)

builder.add_edge(
    "vector_search",
    "generate_answer",
)

builder.add_edge(
    "generate_answer",
    END,
)

app = builder.compile()


# ============================================================
# 25. 테스트 질문
# ============================================================

TEST_QUESTIONS = [
    {
        "level": "1. Graph 1-hop",
        "expected": "graph",
        "question": (
            "김철수가 참여하는 프로젝트는?"
        ),
    },
    {
        "level": "2. Graph Incoming",
        "expected": "graph",
        "question": (
            "VisionGuard에 참여하는 사람은?"
        ),
    },
    {
        "level": "3. Graph Multi-hop",
        "expected": "graph",
        "question": (
            "윤도현이 참여하는 프로젝트가 "
            "속한 팀은 어디야?"
        ),
    },
    {
        "level": "4. Graph 기술 관계",
        "expected": "graph",
        "question": (
            "VisionGuard에서 사용하는 기술은?"
        ),
    },
    {
        "level": "5. Vector 의미 검색",
        "expected": "vector",
        "question": (
            "제품 사진을 분석해서 불량을 "
            "찾는 프로젝트는 뭐야?"
        ),
    },
    {
        "level": "6. Vector 설명 검색",
        "expected": "vector",
        "question": (
            "사내 문서를 검색해서 사용자 질문에 "
            "답하는 프로젝트를 설명해줘."
        ),
    },
    {
        "level": "7. Hybrid 핵심",
        "expected": "hybrid",
        "question": (
            "김철수가 참여하는 프로젝트 중 "
            "이미지 불량 검사와 관련된 "
            "프로젝트를 설명해줘."
        ),
    },
    {
        "level": "8. Hybrid 응용",
        "expected": "hybrid",
        "question": (
            "한서연이 참여하는 프로젝트 중 "
            "고객 문의 답변 지원과 관련된 "
            "프로젝트를 설명해줘."
        ),
    },
    {
        "level": "9. Hybrid 응용",
        "expected": "hybrid",
        "question": (
            "윤도현이 참여하는 프로젝트 중 "
            "서버 장애 감시와 관련된 "
            "프로젝트를 설명해줘."
        ),
    },
]


# ============================================================
# 26. 테스트 질문 출력
# ============================================================


def print_test_questions():

    print("\n" + "=" * 70)
    print("복습용 테스트 질문")
    print("=" * 70)

    for item in TEST_QUESTIONS:
        print()
        print(
            f"[{item['level']}]"
        )
        print(
            "예상 검색:",
            item["expected"],
        )
        print(
            "질문:",
            item["question"],
        )


# ============================================================
# 27. 실행 함수
# ============================================================


def ask(
    question: str,
) -> dict:

    result = app.invoke(
        {
            "question": question
        }
    )

    print("\n" + "=" * 70)
    print("질문")
    print("=" * 70)
    print(question)

    print("\n[질문 분석]")
    print(
        "Entity:",
        result.get(
            "entities",
            [],
        ),
    )
    print(
        "needs_graph:",
        result.get(
            "needs_graph",
        ),
    )
    print(
        "needs_vector:",
        result.get(
            "needs_vector",
        ),
    )
    print(
        "Search Mode:",
        result.get(
            "search_mode",
        ),
    )
    print(
        "Relation:",
        result.get(
            "relation_types",
            [],
        ),
    )
    print(
        "Reason:",
        result.get(
            "analysis_reason",
        ),
    )

    print("\n[Graph 결과 수]")
    print(
        len(
            result.get(
                "graph_results",
                [],
            )
        )
    )

    print("\n[Graph Candidate Project]")
    print(
        result.get(
            "graph_candidate_projects",
            [],
        )
    )

    print("\n[Vector 결과 수]")
    print(
        len(
            result.get(
                "vector_results",
                [],
            )
        )
    )

    print("\n[Graph 검색 결과]")

    graph_results = result.get(
        "graph_results",
        [],
    )

    if not graph_results:
        print("없음")
    else:
        for item in graph_results:
            print(
                f"{item['source']} "
                f"--{item['relation']}--> "
                f"{item['target']} "
                f"(hop={item['hop']})"
            )

    print("\n[Vector 검색 결과]")

    vector_results = result.get(
        "vector_results",
        [],
    )

    if not vector_results:
        print("없음")
    else:
        for item in vector_results:
            print(
                f"[{item['rank']}] "
                f"{item['title']} "
                f"(distance={item['distance']})"
            )

    print("\n[최종 답변]")
    print(
        result["answer"]
    )

    return result


# ============================================================
# 28. Console Program
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "LangChain + LangGraph + "
        "Knowledge Graph + Gemini Review"
    )
    print(
        "종료하려면 exit를 입력하세요."
    )

    print_test_questions()

    while True:

        print()

        question = input(
            "질문 > "
        ).strip()

        if question.lower() in {
            "exit",
            "quit",
            "종료",
        }:
            print(
                "프로그램을 종료합니다."
            )
            break

        if not question:
            continue

        try:
            ask(
                question
            )

        except Exception as error:
            print()
            print("[오류]")
            print(error)
