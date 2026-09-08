import json
import os

from pathlib import Path

import chromadb
import networkx as nx

from dotenv import load_dotenv

from google import genai
from google.genai import types

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# 1. 환경변수
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ENV_PATH = BASE_DIR / "../.env"
load_dotenv(dotenv_path=ENV_PATH)


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


if not GEMINI_API_KEY:

    raise ValueError(
        "GEMINI_API_KEY가 없습니다."
    )


# ============================================================
# 2. Gemini Client
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# 3. 모델
# ============================================================

GENERATION_MODEL = (
    "gemini-3.7-flash"
)


EMBEDDING_MODEL = (
    "gemini-embedding-2"
)


EMBEDDING_DIMENSION = 768


# ============================================================
# 4. 검색 설정
# ============================================================
#
# VectorDB에서는 5개 후보 검색
#
# Hybrid Score 이후에도
# 최대 5개를 LLM Reranker에 전달
#
# 최종적으로 Gemini 답변에는
# 상위 3개만 전달
#
# ============================================================

VECTOR_TOP_K = 5

LLM_RERANK_TOP_K = 5

FINAL_TOP_N = 3


# ============================================================
# 5. LLM 관련성 최소 점수
# ============================================================
#
# 0 ~ 100 중
# 50점 이상만 최종 Evidence 후보로 사용한다.
#
# 이것도 절대적인 기준은 아니다.
# 실습용 기준이다.
#
# ============================================================

MIN_LLM_RELEVANCE_SCORE = 50


# ============================================================
# 6. 경로
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent


DATA_DIR = (
    BASE_DIR
    / "data"
)


GRAPH_JSON_PATH = (
    DATA_DIR
    / "knowledge_graph.json"
)


CHROMA_DIR = (
    DATA_DIR
    / "chroma_hybrid_db"
)


# ============================================================
# 7. 파일 확인
# ============================================================

if not GRAPH_JSON_PATH.exists():

    raise FileNotFoundError(
        "knowledge_graph.json이 없습니다.\n"
        f"{GRAPH_JSON_PATH}"
    )


if not CHROMA_DIR.exists():

    raise FileNotFoundError(
        "ChromaDB가 없습니다.\n"
        "먼저 hybridRagEx01.py를 실행하세요."
    )


# ============================================================
# 8. Knowledge Graph 읽기
# ============================================================

with open(
    GRAPH_JSON_PATH,
    "r",
    encoding="utf-8",
) as file:

    graph_data = json.load(
        file
    )


# ============================================================
# 9. NetworkX Graph 복원
# ============================================================

graph = nx.MultiDiGraph()


for node in graph_data[
    "nodes"
]:

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


for relation in graph_data[
    "relations"
]:

    graph.add_edge(

        relation["source"],

        relation["target"],

        key=relation[
            "edge_id"
        ],

        relation=relation[
            "relation"
        ],

        source_document=relation[
            "source_document"
        ],
    )


# ============================================================
# 10. ChromaDB 연결
# ============================================================

chroma_client = (
    chromadb.PersistentClient(

        path=str(
            CHROMA_DIR
        )
    )
)


COLLECTION_NAME = (
    "hybrid_rag_documents"
)


try:

    collection = (
        chroma_client
        .get_collection(
            name=COLLECTION_NAME
        )
    )

except Exception as error:

    raise RuntimeError(
        "ChromaDB Collection을 찾지 못했습니다.\n"
        "먼저 hybridRagEx01.py를 실행하세요."
    ) from error


if collection.count() == 0:

    raise RuntimeError(
        "ChromaDB에 저장된 문서가 없습니다."
    )


# ============================================================
# 11. Graph Schema
# ============================================================

available_entities = list(
    graph.nodes()
)


available_relations = sorted(

    {

        data.get(
            "relation",
            ""
        )

        for (
            source,
            target,
            edge_key,
            data,
        ) in graph.edges(
            keys=True,
            data=True,
        )

        if data.get(
            "relation",
            ""
        )
    }
)


# ============================================================
# 12. Graph Query Plan
# ============================================================

class GraphQueryPlan(
    BaseModel
):

    start_entities: list[str] = Field(
        description=(
            "Graph 탐색을 시작할 Entity 목록"
        )
    )

    relation_path: list[str] = Field(
        description=(
            "질문에 답하기 위해 순서대로 "
            "따라가야 하는 Relation 목록"
        )
    )


# ============================================================
# 13. 질문 → Graph Query Plan
# ============================================================

def create_graph_query_plan(
    question: str,
) -> GraphQueryPlan:

    entity_text = "\n".join(

        f"- {entity}"

        for entity
        in available_entities
    )


    relation_text = "\n".join(

        f"- {relation}"

        for relation
        in available_relations
    )


    prompt = f"""
사용자 질문을 Knowledge Graph 검색용
Query Plan으로 변환하세요.


[사용 가능한 Entity]

{entity_text}


[사용 가능한 Relation]

{relation_text}


반환할 정보:

1. start_entities
Graph 탐색을 시작할 Entity

2. relation_path
질문에 답하기 위해
순서대로 따라가야 하는 Relation


예:

질문:
철수가 근무하는 회사는 어디에 있어?

start_entities:
["철수"]

relation_path:
["WORKS_AT", "LOCATED_IN"]


규칙:

1. 제공된 Entity만 사용하세요.
2. 제공된 Relation만 사용하세요.
3. Relation 순서가 중요합니다.
4. 필요 없는 Relation은 추가하지 마세요.
5. 같은 Relation이 연속해서 필요한 경우
   중복해서 사용할 수 있습니다.
6. 판단할 수 없다면 빈 리스트를 반환하세요.


[질문]

{question}
"""


    interaction = (
        client.interactions.create(

            model=GENERATION_MODEL,

            input=prompt,

            response_format={

                "type":
                    "text",

                "mime_type":
                    "application/json",

                "schema":
                    GraphQueryPlan
                    .model_json_schema(),
            },
        )
    )


    result = (
        GraphQueryPlan
        .model_validate_json(
            interaction.output_text
        )
    )


    # ========================================================
    # Entity 검증
    # ========================================================

    valid_entities = []


    for entity in (
        result.start_entities
    ):

        if not graph.has_node(
            entity
        ):

            continue


        if entity in valid_entities:

            continue


        valid_entities.append(
            entity
        )


    # ========================================================
    # Relation 검증
    # ========================================================

    valid_relations = []


    for relation in (
        result.relation_path
    ):

        if (
            relation
            not in available_relations
        ):

            continue


        valid_relations.append(
            relation
        )


    return GraphQueryPlan(

        start_entities=(
            valid_entities
        ),

        relation_path=(
            valid_relations
        ),
    )


# ============================================================
# 14. Relation 하나 따라가기
# ============================================================

def follow_relation(
    current_node: str,
    relation_name: str,
):

    results = []


    # ========================================================
    # Outgoing
    # ========================================================

    for (
        source,
        target,
        edge_key,
        data,
    ) in graph.out_edges(

        current_node,

        keys=True,

        data=True,
    ):

        if (
            data.get(
                "relation"
            )
            != relation_name
        ):

            continue


        results.append(

            {
                "next_node":
                    target,

                "edge": {

                    "edge_id":
                        edge_key,

                    "source":
                        source,

                    "relation":
                        data.get(
                            "relation",
                            ""
                        ),

                    "target":
                        target,

                    "source_document":
                        data.get(
                            "source_document",
                            ""
                        ),

                    "traversal_direction":
                        "OUT",
                },
            }
        )


    # ========================================================
    # Incoming
    # ========================================================

    for (
        source,
        target,
        edge_key,
        data,
    ) in graph.in_edges(

        current_node,

        keys=True,

        data=True,
    ):

        if (
            data.get(
                "relation"
            )
            != relation_name
        ):

            continue


        results.append(

            {
                "next_node":
                    source,

                "edge": {

                    "edge_id":
                        edge_key,

                    "source":
                        source,

                    "relation":
                        data.get(
                            "relation",
                            ""
                        ),

                    "target":
                        target,

                    "source_document":
                        data.get(
                            "source_document",
                            ""
                        ),

                    "traversal_direction":
                        "IN",
                },
            }
        )


    return results


# ============================================================
# 15. Ordered Relation Path 탐색
# ============================================================

def traverse_relation_path(
    start_entity: str,
    relation_path: list[str],
):

    frontier = [

        {
            "current_node":
                start_entity,

            "edges":
                [],
        }

    ]


    for relation_name in (
        relation_path
    ):

        next_frontier = []


        for item in frontier:

            matches = (
                follow_relation(

                    item[
                        "current_node"
                    ],

                    relation_name,
                )
            )


            for match in matches:

                next_frontier.append(

                    {
                        "current_node":
                            match[
                                "next_node"
                            ],

                        "edges":
                            (
                                item["edges"]
                                +
                                [
                                    match[
                                        "edge"
                                    ]
                                ]
                            ),
                    }
                )


        if not next_frontier:

            return []


        frontier = (
            next_frontier
        )


    paths = []


    for item in frontier:

        paths.append(

            {
                "start_entity":
                    start_entity,

                "end_entity":
                    item[
                        "current_node"
                    ],

                "edges":
                    item["edges"],
            }
        )


    return paths


# ============================================================
# 16. Graph Path 검색
# ============================================================

def retrieve_graph_paths(
    start_entities: list[str],
    relation_path: list[str],
):

    all_paths = []


    for entity in (
        start_entities
    ):

        paths = (
            traverse_relation_path(

                entity,

                relation_path,
            )
        )


        all_paths.extend(
            paths
        )


    return all_paths


# ============================================================
# 17. Graph Evidence Document ID
# ============================================================

def collect_graph_document_ids(
    graph_paths,
):

    document_ids = []


    for path in graph_paths:

        for edge in path[
            "edges"
        ]:

            doc_id = edge.get(
                "source_document",
                ""
            )


            if not doc_id:

                continue


            if doc_id in document_ids:

                continue


            document_ids.append(
                doc_id
            )


    return document_ids


# ============================================================
# 18. Graph Evidence 원문 가져오기
# ============================================================
#
# ChromaDB Semantic Search가 아니다.
#
# Document ID로 정확하게 가져온다.
#
# ============================================================

def retrieve_graph_documents(
    document_ids,
):

    if not document_ids:

        return []


    result = collection.get(

        ids=document_ids,

        include=[
            "documents",
            "metadatas",
        ],
    )


    ids = (
        result.get(
            "ids",
            []
        )
        or []
    )


    documents = (
        result.get(
            "documents",
            []
        )
        or []
    )


    metadatas = (
        result.get(
            "metadatas",
            []
        )
        or []
    )


    result_map = {}


    for index, doc_id in enumerate(
        ids
    ):

        result_map[
            doc_id
        ] = {

            "doc_id":
                doc_id,

            "text":
                documents[index],

            "metadata":
                metadatas[index],
        }


    # Graph에서 발견한 순서 유지
    ordered_results = []


    for doc_id in document_ids:

        if doc_id not in result_map:

            continue


        ordered_results.append(
            result_map[
                doc_id
            ]
        )


    return ordered_results


# ============================================================
# 19. Vector Query 준비
# ============================================================

def prepare_vector_query(
    question: str,
):

    return (
        "task: search result | "
        f"query: {question}"
    )


# ============================================================
# 20. Query Embedding
# ============================================================

def create_query_embedding(
    question: str,
):

    query_text = (
        prepare_vector_query(
            question
        )
    )


    result = (
        client.models.embed_content(

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


    return list(
        result.embeddings[0].values
    )


# ============================================================
# 21. Vector Retrieval
# ============================================================

def retrieve_vector_documents(
    question: str,
    top_k: int = 5,
):

    query_embedding = (
        create_query_embedding(
            question
        )
    )


    result = collection.query(

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


    ids = (
        result["ids"][0]
    )


    documents = (
        result["documents"][0]
    )


    metadatas = (
        result["metadatas"][0]
    )


    distances = (
        result["distances"][0]
    )


    results = []


    for index, doc_id in enumerate(
        ids
    ):

        results.append(

            {
                "doc_id":
                    doc_id,

                "text":
                    documents[index],

                "metadata":
                    metadatas[index],

                "vector_rank":
                    index + 1,

                "distance":
                    distances[index],
            }
        )


    return results


# ============================================================
# 22. Evidence Fusion
# ============================================================

def fuse_evidence(
    graph_documents,
    vector_documents,
):

    fused = []

    document_map = {}


    # ========================================================
    # Graph Evidence
    # ========================================================

    for graph_rank, document in enumerate(
        graph_documents,
        start=1,
    ):

        item = {

            "doc_id":
                document["doc_id"],

            "text":
                document["text"],

            "metadata":
                document["metadata"],

            "retrieval_sources":
                [
                    "graph"
                ],

            "graph_rank":
                graph_rank,

            "vector_rank":
                None,

            "distance":
                None,
        }


        fused.append(
            item
        )


        document_map[
            document["doc_id"]
        ] = item


    # ========================================================
    # Vector Evidence
    # ========================================================

    for document in vector_documents:

        doc_id = document[
            "doc_id"
        ]


        # ----------------------------------------------------
        # Graph에도 존재
        # ----------------------------------------------------

        if doc_id in document_map:

            item = document_map[
                doc_id
            ]


            if (
                "vector"
                not in item[
                    "retrieval_sources"
                ]
            ):

                item[
                    "retrieval_sources"
                ].append(
                    "vector"
                )


            item[
                "vector_rank"
            ] = document[
                "vector_rank"
            ]


            item[
                "distance"
            ] = document[
                "distance"
            ]


            continue


        # ----------------------------------------------------
        # Vector Only
        # ----------------------------------------------------

        item = {

            "doc_id":
                doc_id,

            "text":
                document["text"],

            "metadata":
                document["metadata"],

            "retrieval_sources":
                [
                    "vector"
                ],

            "graph_rank":
                None,

            "vector_rank":
                document[
                    "vector_rank"
                ],

            "distance":
                document[
                    "distance"
                ],
        }


        fused.append(
            item
        )


        document_map[
            doc_id
        ] = item


    return fused


# ============================================================
# 23. Hybrid Score
# ============================================================
#
# 실습 04에서 사용했던
# Rule-based Score이다.
#
# 이것은 확률이나 정확도가 아니다.
#
# Retrieval 우선순위를 만들기 위한
# 실습용 점수이다.
#
# ============================================================

def calculate_hybrid_score(
    document,
):

    sources = document[
        "retrieval_sources"
    ]


    graph_rank = document[
        "graph_rank"
    ]


    vector_rank = document[
        "vector_rank"
    ]


    distance = document[
        "distance"
    ]


    # ========================================================
    # Graph 포함
    # ========================================================

    if "graph" in sources:

        graph_presence_score = 2.0

    else:

        graph_presence_score = 0.0


    # ========================================================
    # Graph + Vector 양쪽
    # ========================================================

    if (
        "graph" in sources
        and
        "vector" in sources
    ):

        both_source_bonus = 1.0

    else:

        both_source_bonus = 0.0


    # ========================================================
    # Graph Rank
    # ========================================================

    if graph_rank is not None:

        graph_rank_score = (
            0.5
            / graph_rank
        )

    else:

        graph_rank_score = 0.0


    # ========================================================
    # Vector Rank
    # ========================================================

    if vector_rank is not None:

        vector_rank_score = (
            0.75
            / vector_rank
        )

    else:

        vector_rank_score = 0.0


    # ========================================================
    # Vector Distance
    # ========================================================

    if distance is not None:

        safe_distance = max(
            0.0,
            float(distance),
        )


        vector_distance_score = (

            0.25

            * (

                1.0
                /
                (
                    1.0
                    + safe_distance
                )
            )
        )

    else:

        vector_distance_score = 0.0


    # ========================================================
    # 최종
    # ========================================================

    hybrid_score = (

        graph_presence_score

        + both_source_bonus

        + graph_rank_score

        + vector_rank_score

        + vector_distance_score
    )


    return {

        "graph_presence_score":
            graph_presence_score,

        "both_source_bonus":
            both_source_bonus,

        "graph_rank_score":
            graph_rank_score,

        "vector_rank_score":
            vector_rank_score,

        "vector_distance_score":
            vector_distance_score,

        "hybrid_score":
            hybrid_score,
    }


# ============================================================
# 24. 1차 Hybrid Reranking
# ============================================================

def rerank_by_hybrid_score(
    fused_documents,
):

    results = []


    for document in (
        fused_documents
    ):

        item = document.copy()


        score_detail = (
            calculate_hybrid_score(
                item
            )
        )


        item[
            "score_detail"
        ] = score_detail


        item[
            "hybrid_score"
        ] = score_detail[
            "hybrid_score"
        ]


        results.append(
            item
        )


    # ========================================================
    # 높은 점수 우선
    # ========================================================

    results.sort(

        key=lambda item: (
            item[
                "hybrid_score"
            ]
        ),

        reverse=True,
    )


    # ========================================================
    # Hybrid Rank
    # ========================================================

    for index, item in enumerate(
        results,
        start=1,
    ):

        item[
            "hybrid_rank"
        ] = index


    return results


# ============================================================
# 25. LLM Reranker 출력 구조
# ============================================================

class EvidenceEvaluation(
    BaseModel
):

    doc_id: str = Field(
        description=(
            "평가한 문서의 Document ID"
        )
    )


    relevance_score: int = Field(
        ge=0,
        le=100,
        description=(
            "사용자 질문과 문서의 관련성 점수. "
            "0은 무관, 100은 매우 직접적인 관련."
        ),
    )


    is_relevant: bool = Field(
        description=(
            "질문에 답하는 데 실제로 "
            "유용한 문서인지 여부"
        )
    )


    reason: str = Field(
        description=(
            "관련성 점수를 부여한 간단한 이유"
        )
    )


class LLMRerankResult(
    BaseModel
):

    evaluations: list[
        EvidenceEvaluation
    ]


# ============================================================
# 26. LLM Reranker Prompt 생성
# ============================================================

def build_llm_rerank_prompt(
    question: str,
    candidate_documents,
):

    blocks = []


    for document in (
        candidate_documents
    ):

        source_text = ", ".join(
            document[
                "retrieval_sources"
            ]
        )


        block = f"""
[DOCUMENT]

Document ID:
{document['doc_id']}

검색 출처:
{source_text}

원문:
{document['text']}
""".strip()


        blocks.append(
            block
        )


    candidate_text = "\n\n".join(
        blocks
    )


    return f"""
당신은 RAG 검색 결과를 재정렬하는
Reranker입니다.

사용자의 질문과 각 문서의 실제 관련성을
평가하세요.


==================================================
[사용자 질문]
==================================================

{question}


==================================================
[후보 문서]
==================================================

{candidate_text}


==================================================
[평가 기준]
==================================================

각 문서에 대해 다음을 판단하세요.

1. relevance_score

0 ~ 100 사이 정수입니다.

100:
질문에 직접 답하기 위해 반드시 필요한 문서

80 ~ 99:
질문에 매우 직접적으로 관련된 문서

60 ~ 79:
답변에 도움이 되는 관련 문서

40 ~ 59:
주제는 관련 있지만 직접적인 답변 근거는 약한 문서

0 ~ 39:
질문과 거의 관계없는 문서


2. is_relevant

실제 최종 답변을 만드는 데
사용할 가치가 있다면 true,
아니면 false입니다.


3. reason

왜 그렇게 평가했는지
짧게 설명하세요.


중요한 규칙:

1. 검색 순위가 높다는 이유만으로
   높은 점수를 주면 안 됩니다.

2. Graph 검색에서 나왔다는 이유만으로
   높은 점수를 주면 안 됩니다.

3. Vector 검색에서 나왔다는 이유만으로
   높은 점수를 주면 안 됩니다.

4. 오직 사용자 질문과
   문서 원문의 실제 관련성을 평가하세요.

5. 사실의 진실성이나 확률을 평가하는 것이 아닙니다.

6. relevance_score는
   "질문과의 관련성"을 의미합니다.

7. 모든 후보 문서를
   정확히 한 번씩 평가하세요.

8. Document ID는 변경하지 마세요.
"""


# ============================================================
# 27. Gemini LLM Reranking
# ============================================================

def rerank_with_llm(
    question: str,
    candidate_documents,
):

    if not candidate_documents:

        return []


    prompt = (
        build_llm_rerank_prompt(

            question,

            candidate_documents,
        )
    )


    # ========================================================
    # Structured Output
    # ========================================================

    interaction = (
        client.interactions.create(

            model=GENERATION_MODEL,

            input=prompt,

            response_format={

                "type":
                    "text",

                "mime_type":
                    "application/json",

                "schema":
                    LLMRerankResult
                    .model_json_schema(),
            },
        )
    )


    result = (
        LLMRerankResult
        .model_validate_json(

            interaction.output_text
        )
    )


    # ========================================================
    # 원본 Candidate Map
    # ========================================================

    candidate_map = {

        document["doc_id"]:
            document

        for document
        in candidate_documents
    }


    # ========================================================
    # Gemini 평가 결과 Map
    # ========================================================

    evaluation_map = {}


    for evaluation in (
        result.evaluations
    ):

        # ----------------------------------------------------
        # 존재하지 않는 Document ID는 무시
        # ----------------------------------------------------

        if (
            evaluation.doc_id
            not in candidate_map
        ):

            continue


        evaluation_map[
            evaluation.doc_id
        ] = evaluation


    # ========================================================
    # 평가 결과를 원본 문서에 결합
    # ========================================================

    reranked = []


    for document in (
        candidate_documents
    ):

        item = document.copy()


        doc_id = item[
            "doc_id"
        ]


        evaluation = (
            evaluation_map.get(
                doc_id
            )
        )


        # ----------------------------------------------------
        # Gemini가 실수로 평가를 누락했을 경우
        # ----------------------------------------------------

        if evaluation is None:

            item[
                "llm_relevance_score"
            ] = 0


            item[
                "llm_is_relevant"
            ] = False


            item[
                "llm_reason"
            ] = (
                "LLM 평가 결과에 "
                "해당 문서가 포함되지 않았습니다."
            )


        else:

            item[
                "llm_relevance_score"
            ] = (
                evaluation
                .relevance_score
            )


            item[
                "llm_is_relevant"
            ] = (
                evaluation
                .is_relevant
            )


            item[
                "llm_reason"
            ] = (
                evaluation.reason
            )


        reranked.append(
            item
        )


    # ========================================================
    # LLM 관련성 점수로 재정렬
    # ========================================================
    #
    # 동일 점수인 경우에는
    # 이전 Hybrid Rank가 높은 문서를 우선한다.
    #
    # ========================================================

    reranked.sort(

        key=lambda item: (

            -item[
                "llm_relevance_score"
            ],

            item[
                "hybrid_rank"
            ],
        )
    )


    # ========================================================
    # LLM Rank 부여
    # ========================================================

    for index, item in enumerate(
        reranked,
        start=1,
    ):

        item[
            "llm_rank"
        ] = index


    return reranked


# ============================================================
# 28. 최종 Evidence 선택
# ============================================================

def select_final_evidence(
    llm_reranked_documents,
    top_n: int = 3,
    min_score: int = 50,
):

    selected = []


    for document in (
        llm_reranked_documents
    ):

        # ----------------------------------------------------
        # LLM이 Relevant라고 판단
        # ----------------------------------------------------

        if not document[
            "llm_is_relevant"
        ]:

            continue


        # ----------------------------------------------------
        # 최소 관련성 점수
        # ----------------------------------------------------

        if (
            document[
                "llm_relevance_score"
            ]
            < min_score
        ):

            continue


        selected.append(
            document
        )


        if (
            len(selected)
            >= top_n
        ):

            break


    return selected


# ============================================================
# 29. Graph Context
# ============================================================

def build_graph_context(
    graph_paths,
):

    if not graph_paths:

        return (
            "Graph 검색 결과가 없습니다."
        )


    blocks = []


    for path_index, path in enumerate(
        graph_paths,
        start=1,
    ):

        lines = [

            (
                f"[GRAPH PATH "
                f"{path_index}]"
            )

        ]


        for edge in path[
            "edges"
        ]:

            lines.append(

                (
                    f"{edge['source']} "
                    f"-- "
                    f"{edge['relation']} "
                    f"--> "
                    f"{edge['target']} "
                    f"(출처: "
                    f"{edge['source_document']})"
                )
            )


        blocks.append(

            "\n".join(
                lines
            )
        )


    return "\n\n".join(
        blocks
    )


# ============================================================
# 30. 최종 Evidence Context
# ============================================================

def build_final_evidence_context(
    documents,
):

    if not documents:

        return (
            "최종 Evidence가 없습니다."
        )


    blocks = []


    for document in documents:

        source_text = " + ".join(

            source.upper()

            for source in (
                document[
                    "retrieval_sources"
                ]
            )
        )


        block = f"""
[FINAL EVIDENCE {document['llm_rank']}]

Document ID:
{document['doc_id']}

검색 출처:
{source_text}

Hybrid Rank:
{document['hybrid_rank']}

Hybrid Score:
{document['hybrid_score']:.4f}

LLM Relevance Score:
{document['llm_relevance_score']}

LLM 평가 이유:
{document['llm_reason']}

원문:
{document['text']}
""".strip()


        blocks.append(
            block
        )


    return "\n\n".join(
        blocks
    )


# ============================================================
# 31. 최종 Gemini 답변
# ============================================================

def generate_answer(
    question: str,
    graph_context: str,
    evidence_context: str,
):

    prompt = f"""
당신은 Knowledge Graph와 VectorDB를
결합한 Hybrid RAG 시스템입니다.

다음 검색 근거를 이용해서
사용자 질문에 답하세요.


==================================================
[Graph Context]
==================================================

{graph_context}


==================================================
[Final Evidence]
==================================================

{evidence_context}


==================================================
[질문]
==================================================

{question}


==================================================
[답변 규칙]
==================================================

1. 제공된 Graph와 Evidence에서
   확인되는 사실만 사용하세요.

2. Graph Context는 Entity 사이의
   관계 구조를 이해하는 데 사용하세요.

3. Final Evidence의 원문을
   사실 확인의 주요 근거로 사용하세요.

4. LLM Relevance Score는
   검색 우선순위일 뿐
   사실의 확률이나 신뢰도가 아닙니다.

5. 점수가 높다는 이유만으로
   원문에 없는 사실을 추가하지 마세요.

6. 검색 근거에 없는 내용은
   추측하지 마세요.

7. 답변 마지막에는 실제로 사용한
   Document ID를 표시하세요.

8. 충분한 근거가 없다면

"제공된 검색 결과만으로는 답할 수 없습니다."

라고 답하세요.
"""


    response = (
        client.models.generate_content(

            model=GENERATION_MODEL,

            contents=prompt,
        )
    )


    return response.text


# ============================================================
# 32. 전체 Hybrid RAG Pipeline
# ============================================================

def hybrid_rag(
    question: str,
):

    print("\n")

    print("#" * 70)
    print("사용자 질문")
    print("#" * 70)

    print(
        question
    )


    # ========================================================
    # STEP 1
    # Graph Query Plan
    # ========================================================

    query_plan = (
        create_graph_query_plan(
            question
        )
    )


    print("\n")

    print("=" * 70)
    print("STEP 1 - Graph Query Plan")
    print("=" * 70)


    print(
        "Start Entity:",
        query_plan.start_entities
    )


    print(
        "Relation Path:",
        query_plan.relation_path
    )


    # ========================================================
    # STEP 2
    # Graph Retrieval
    # ========================================================

    graph_paths = (
        retrieve_graph_paths(

            query_plan.start_entities,

            query_plan.relation_path,
        )
    )


    print("\n")

    print("=" * 70)
    print("STEP 2 - Graph Retrieval")
    print("=" * 70)


    if graph_paths:

        for path_index, path in enumerate(
            graph_paths,
            start=1,
        ):

            print()

            print(
                f"[PATH {path_index}]"
            )


            for edge in path[
                "edges"
            ]:

                print(
                    edge["source"],
                    "--",
                    edge["relation"],
                    "-->",
                    edge["target"],
                    "|",
                    edge[
                        "source_document"
                    ],
                )

    else:

        print(
            "Graph Path 없음"
        )


    graph_context = (
        build_graph_context(
            graph_paths
        )
    )


    # ========================================================
    # STEP 3
    # Graph Evidence
    # ========================================================

    graph_document_ids = (
        collect_graph_document_ids(
            graph_paths
        )
    )


    graph_documents = (
        retrieve_graph_documents(
            graph_document_ids
        )
    )


    print("\n")

    print("=" * 70)
    print("STEP 3 - Graph Evidence")
    print("=" * 70)


    if graph_documents:

        for document in (
            graph_documents
        ):

            print(
                document["doc_id"],
                ":",
                document["text"],
            )

    else:

        print(
            "Graph Evidence 없음"
        )


    # ========================================================
    # STEP 4
    # Vector Retrieval
    # ========================================================

    vector_documents = (
        retrieve_vector_documents(

            question,

            top_k=VECTOR_TOP_K,
        )
    )


    print("\n")

    print("=" * 70)
    print("STEP 4 - Vector Retrieval")
    print("=" * 70)


    for document in (
        vector_documents
    ):

        print(
            (
                f"Rank "
                f"{document['vector_rank']}"
            ),
            "|",
            document["doc_id"],
            "| Distance:",
            round(
                float(
                    document[
                        "distance"
                    ]
                ),
                4,
            ),
        )


    # ========================================================
    # STEP 5
    # Evidence Fusion
    # ========================================================

    fused_documents = (
        fuse_evidence(

            graph_documents,

            vector_documents,
        )
    )


    # ========================================================
    # STEP 6
    # Hybrid Score Reranking
    # ========================================================

    hybrid_reranked = (
        rerank_by_hybrid_score(
            fused_documents
        )
    )


    print("\n")

    print("=" * 70)
    print("STEP 5 - Hybrid Score Reranking")
    print("=" * 70)


    for document in (
        hybrid_reranked
    ):

        print()


        print(
            (
                f"[HYBRID RANK "
                f"{document['hybrid_rank']}]"
            )
        )


        print(
            "문서:",
            document["doc_id"]
        )


        print(
            "출처:",
            document[
                "retrieval_sources"
            ]
        )


        print(
            "Hybrid Score:",
            round(
                document[
                    "hybrid_score"
                ],
                4,
            )
        )


    # ========================================================
    # STEP 7
    # LLM Reranking 후보
    # ========================================================

    llm_candidates = (

        hybrid_reranked[
            :LLM_RERANK_TOP_K
        ]
    )


    # ========================================================
    # STEP 8
    # Gemini LLM Reranker
    # ========================================================

    llm_reranked = (
        rerank_with_llm(

            question,

            llm_candidates,
        )
    )


    print("\n")

    print("=" * 70)
    print("STEP 6 - Gemini LLM Reranking")
    print("=" * 70)


    for document in (
        llm_reranked
    ):

        print()


        print(
            (
                f"[LLM RANK "
                f"{document['llm_rank']}]"
            )
        )


        print(
            "문서:",
            document["doc_id"]
        )


        print(
            "Hybrid Rank:",
            document[
                "hybrid_rank"
            ]
        )


        print(
            "LLM 관련성 점수:",
            document[
                "llm_relevance_score"
            ]
        )


        print(
            "Relevant:",
            document[
                "llm_is_relevant"
            ]
        )


        print(
            "이유:",
            document[
                "llm_reason"
            ]
        )


    # ========================================================
    # STEP 9
    # Final Evidence
    # ========================================================

    final_documents = (
        select_final_evidence(

            llm_reranked,

            top_n=FINAL_TOP_N,

            min_score=(
                MIN_LLM_RELEVANCE_SCORE
            ),
        )
    )


    print("\n")

    print("=" * 70)
    print("STEP 7 - Final Evidence")
    print("=" * 70)


    if final_documents:

        for document in (
            final_documents
        ):

            print()

            print(
                (
                    f"LLM Rank "
                    f"{document['llm_rank']}"
                )
            )


            print(
                document["doc_id"]
            )


            print(
                (
                    f"관련성 점수: "
                    f"{document['llm_relevance_score']}"
                )
            )


            print(
                document["text"]
            )

    else:

        print(
            "최종 Evidence가 없습니다."
        )


    # ========================================================
    # STEP 10
    # Final Evidence Context
    # ========================================================

    evidence_context = (
        build_final_evidence_context(
            final_documents
        )
    )


    # ========================================================
    # STEP 11
    # Final Answer
    # ========================================================

    answer = (
        generate_answer(

            question,

            graph_context,

            evidence_context,
        )
    )


    print("\n")

    print("=" * 70)
    print("STEP 8 - Gemini Answer")
    print("=" * 70)


    print()

    print(
        answer
    )


    # ========================================================
    # 결과 반환
    # ========================================================

    return {

        "question":
            question,

        "query_plan":
            query_plan.model_dump(),

        "graph_paths":
            graph_paths,

        "graph_documents":
            graph_documents,

        "vector_documents":
            vector_documents,

        "fused_documents":
            fused_documents,

        "hybrid_reranked":
            hybrid_reranked,

        "llm_candidates":
            llm_candidates,

        "llm_reranked":
            llm_reranked,

        "final_documents":
            final_documents,

        "graph_context":
            graph_context,

        "evidence_context":
            evidence_context,

        "answer":
            answer,
    }


# ============================================================
# 33. 테스트
# ============================================================

question = (
    "철수가 근무하는 회사는 "
    "어디에 있어?"
)


result = hybrid_rag(
    question
)