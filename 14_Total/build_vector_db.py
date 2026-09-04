import json
import os

from pathlib import Path

import chromadb

from dotenv import load_dotenv

from google import genai
from google.genai import types


# ============================================================
# 1. 환경변수
# ============================================================

load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


if not GEMINI_API_KEY:

    raise ValueError(
        "GEMINI_API_KEY가 없습니다.\n"
        ".env 파일을 확인하세요."
    )


# ============================================================
# 2. Gemini Client
# ============================================================

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# 3. Embedding 모델 설정
# ============================================================

EMBEDDING_MODEL = (
    "gemini-embedding-2"
)


# ------------------------------------------------------------
# Gemini Embedding 2는
#
# 768
# 1536
# 3072
#
# 등을 사용할 수 있다.
#
# 이번 실습에서는 저장 공간과 검색 속도를 고려해
# 768차원을 사용한다.
# ------------------------------------------------------------

EMBEDDING_DIMENSION = 768


# ============================================================
# 4. 한 번에 Embedding할 문서 수
# ============================================================
#
# 문서는 총 70개다.
#
# 하나씩 요청하면 API 호출이 70번 발생한다.
#
# 이번에는 10개씩 묶는다.
#
# 70개
# ↓
# 10개씩
# ↓
# 약 7번 요청
#
# ============================================================

EMBEDDING_BATCH_SIZE = 10


# ============================================================
# 5. 경로 설정
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent


DATA_DIR = (
    BASE_DIR
    / "data"
)


DOCUMENT_PATH = (
    DATA_DIR
    / "documents.json"
)


CHROMA_DIR = (
    DATA_DIR
    / "chroma_db"
)


# ============================================================
# 6. documents.json 확인
# ============================================================

if not DOCUMENT_PATH.exists():

    raise FileNotFoundError(
        "documents.json이 없습니다.\n"
        "먼저 prepare_data.py를 실행하세요.\n\n"
        f"찾은 경로:\n{DOCUMENT_PATH}"
    )


# ============================================================
# 7. documents.json 읽기
# ============================================================

with open(
    DOCUMENT_PATH,
    "r",
    encoding="utf-8",
) as file:

    documents = json.load(
        file
    )


# ============================================================
# 8. 문서 데이터 검증
# ============================================================

if not documents:

    raise ValueError(
        "documents.json에 문서가 없습니다."
    )


print("=" * 70)
print("Document 데이터 확인")
print("=" * 70)


print(
    "문서 수:",
    len(documents)
)


print(
    "첫 번째 문서:"
)


print(
    documents[0]
)


# ============================================================
# 9. 검색용 Document 문자열 만들기
# ============================================================
#
# gemini-embedding-2에서는
# Retrieval 용도의 Text Embedding을 만들 때
#
# Document:
#
# title: 제목 | text: 내용
#
# Query:
#
# task: search result | query: 질문
#
# 구조 사용을 권장한다.
#
# ============================================================

def prepare_document_text(
    title: str,
    text: str,
) -> str:

    return (
        f"title: {title} | "
        f"text: {text}"
    )


# ============================================================
# 10. 검색 Query 문자열
# ============================================================

def prepare_query_text(
    question: str,
) -> str:

    return (
        "task: search result | "
        f"query: {question}"
    )


# ============================================================
# 11. 문자열 → Gemini Content
# ============================================================
#
# 매우 중요
#
# gemini-embedding-2에서
# 여러 문자열을 그냥 list로 전달하면
# 하나의 통합 Embedding으로 처리될 수 있다.
#
# 문서마다 개별 Embedding을 얻으려면
# 각각을 Content 객체로 만들어 전달한다.
#
# ============================================================

def make_content(
    text: str,
) -> types.Content:

    return types.Content(

        parts=[

            types.Part.from_text(
                text=text
            )

        ]
    )


# ============================================================
# 12. 여러 Document Embedding 생성
# ============================================================

def create_document_embeddings(
    document_batch: list[dict],
) -> list[list[float]]:

    # --------------------------------------------------------
    # Gemini API에 전달할 Content 목록
    # --------------------------------------------------------

    contents = []


    for document in document_batch:

        embedding_text = (
            prepare_document_text(

                document["title"],

                document["text"],
            )
        )


        content = make_content(
            embedding_text
        )


        contents.append(
            content
        )


    # --------------------------------------------------------
    # Gemini Embedding
    # --------------------------------------------------------

    result = (
        gemini_client.models.embed_content(

            model=EMBEDDING_MODEL,

            contents=contents,

            config=(
                types.EmbedContentConfig(

                    output_dimensionality=(
                        EMBEDDING_DIMENSION
                    )
                )
            ),
        )
    )


    # --------------------------------------------------------
    # 결과 검증
    # --------------------------------------------------------

    if not result.embeddings:

        raise RuntimeError(
            "Embedding 결과가 없습니다."
        )


    if (
        len(result.embeddings)
        != len(document_batch)
    ):

        raise RuntimeError(
            "입력 문서 수와 Embedding 결과 수가 "
            "일치하지 않습니다.\n"
            f"입력: {len(document_batch)}\n"
            f"출력: {len(result.embeddings)}"
        )


    embeddings = []


    for embedding in (
        result.embeddings
    ):

        vector = list(
            embedding.values
        )


        # ----------------------------------------------------
        # 차원 검증
        # ----------------------------------------------------

        if (
            len(vector)
            != EMBEDDING_DIMENSION
        ):

            raise RuntimeError(
                "Embedding 차원이 올바르지 않습니다.\n"
                f"기대: {EMBEDDING_DIMENSION}\n"
                f"실제: {len(vector)}"
            )


        embeddings.append(
            vector
        )


    return embeddings


# ============================================================
# 13. Query Embedding 생성
# ============================================================

def create_query_embedding(
    question: str,
) -> list[float]:

    query_text = (
        prepare_query_text(
            question
        )
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


    if (
        len(vector)
        != EMBEDDING_DIMENSION
    ):

        raise RuntimeError(
            "Query Embedding 차원이 "
            "올바르지 않습니다."
        )


    return vector


# ============================================================
# 14. ChromaDB Persistent Client
# ============================================================
#
# PersistentClient이므로
# Python 프로그램을 종료해도
# DB가 data/chroma_db에 남는다.
#
# ============================================================

chroma_client = (
    chromadb.PersistentClient(

        path=str(
            CHROMA_DIR
        )
    )
)


# ============================================================
# 15. Collection 생성
# ============================================================

COLLECTION_NAME = (
    "company_knowledge_documents"
)


collection = (
    chroma_client
    .get_or_create_collection(

        name=COLLECTION_NAME,

        metadata={

            "description":
                (
                    "사내 프로젝트 및 "
                    "인력 지식 검색 문서"
                ),

            "embedding_model":
                EMBEDDING_MODEL,

            "embedding_dimension":
                EMBEDDING_DIMENSION,
        },
    )
)


print("\n")
print("=" * 70)
print("ChromaDB")
print("=" * 70)


print(
    "저장 경로:",
    CHROMA_DIR
)


print(
    "Collection:",
    COLLECTION_NAME
)


print(
    "기존 문서 수:",
    collection.count()
)


# ============================================================
# 16. Batch 단위로 Embedding + 저장
# ============================================================

print("\n")
print("=" * 70)
print("Document Embedding 시작")
print("=" * 70)


total_documents = len(
    documents
)


for start_index in range(
    0,
    total_documents,
    EMBEDDING_BATCH_SIZE,
):

    # --------------------------------------------------------
    # Batch 범위
    # --------------------------------------------------------

    end_index = min(

        start_index
        + EMBEDDING_BATCH_SIZE,

        total_documents,
    )


    document_batch = (
        documents[
            start_index:end_index
        ]
    )


    print()


    print(
        (
            f"Embedding 진행: "
            f"{start_index + 1}"
            f" ~ "
            f"{end_index}"
            f" / "
            f"{total_documents}"
        )
    )


    # ========================================================
    # 17. Gemini Embedding 생성
    # ========================================================

    embeddings = (
        create_document_embeddings(
            document_batch
        )
    )


    # ========================================================
    # 18. ChromaDB 저장용 데이터
    # ========================================================

    ids = []

    texts = []

    metadatas = []


    for document in document_batch:

        ids.append(
            document["doc_id"]
        )


        texts.append(
            document["text"]
        )


        # ----------------------------------------------------
        # Metadata
        #
        # 나중에 category 검색이나
        # 결과 확인에 사용한다.
        # ----------------------------------------------------

        metadatas.append(

            {
                "doc_id":
                    document["doc_id"],

                "category":
                    document["category"],

                "title":
                    document["title"],
            }
        )


    # ========================================================
    # 19. ChromaDB Upsert
    # ========================================================
    #
    # upsert
    #
    # ID가 없으면 Insert
    # ID가 있으면 Update
    #
    # 따라서 코드를 다시 실행해도
    # DOC-001 같은 문서가 계속 중복 추가되지 않는다.
    #
    # ========================================================

    collection.upsert(

        ids=ids,

        embeddings=embeddings,

        documents=texts,

        metadatas=metadatas,
    )


    print(
        (
            f"저장 완료: "
            f"{len(document_batch)}개"
        )
    )


# ============================================================
# 20. 최종 저장 결과 확인
# ============================================================

print("\n")
print("=" * 70)
print("VectorDB 구축 완료")
print("=" * 70)


stored_count = (
    collection.count()
)


print(
    "documents.json 문서 수:",
    total_documents
)


print(
    "ChromaDB 문서 수:",
    stored_count
)


if (
    stored_count
    != total_documents
):

    print(
        "\n[주의]"
    )

    print(
        "documents.json 문서 수와 "
        "ChromaDB 문서 수가 다릅니다."
    )

else:

    print(
        "\n70개 문서가 정상적으로 저장되었습니다."
    )


# ============================================================
# 21. 저장된 문서 일부 확인
# ============================================================

print("\n")
print("=" * 70)
print("저장 데이터 일부 확인")
print("=" * 70)


stored_data = collection.get(

    limit=5,

    include=[
        "documents",
        "metadatas",
    ],
)


stored_ids = (
    stored_data.get(
        "ids",
        []
    )
    or []
)


stored_documents = (
    stored_data.get(
        "documents",
        []
    )
    or []
)


stored_metadatas = (
    stored_data.get(
        "metadatas",
        []
    )
    or []
)


for index in range(
    len(stored_ids)
):

    print()


    print(
        f"[{index + 1}]"
    )


    print(
        "ID:",
        stored_ids[index]
    )


    print(
        "Title:",
        stored_metadatas[index][
            "title"
        ]
    )


    print(
        "Category:",
        stored_metadatas[index][
            "category"
        ]
    )


    print(
        "Text:",
        stored_documents[index]
    )


# ============================================================
# 22. Vector Search 테스트
# ============================================================
#
# 아직 최종 응용 프로그램은 아니다.
#
# 지금 만든 VectorDB가
# 제대로 검색되는지만 확인한다.
#
# ============================================================

test_question = (
    "제품 이미지를 분석해서 "
    "불량을 찾는 프로젝트는 뭐야?"
)


print("\n")
print("#" * 70)
print("Vector Search 테스트")
print("#" * 70)


print(
    "질문:",
    test_question
)


# ============================================================
# 23. 질문 Embedding
# ============================================================

query_embedding = (
    create_query_embedding(
        test_question
    )
)


print(
    "Query Embedding 차원:",
    len(query_embedding)
)


# ============================================================
# 24. ChromaDB 검색
# ============================================================
#
# 상위 5개 문서
#
# ============================================================

search_result = collection.query(

    query_embeddings=[
        query_embedding
    ],

    n_results=5,

    include=[
        "documents",
        "metadatas",
        "distances",
    ],
)


# ============================================================
# 25. 검색 결과 정리
# ============================================================

result_ids = (
    search_result[
        "ids"
    ][0]
)


result_documents = (
    search_result[
        "documents"
    ][0]
)


result_metadatas = (
    search_result[
        "metadatas"
    ][0]
)


result_distances = (
    search_result[
        "distances"
    ][0]
)


# ============================================================
# 26. 결과 출력
# ============================================================

print("\n")
print("=" * 70)
print("검색 결과")
print("=" * 70)


for index in range(
    len(result_ids)
):

    print()


    print(
        (
            f"[검색 순위 "
            f"{index + 1}]"
        )
    )


    print(
        "Document ID:",
        result_ids[index]
    )


    print(
        "Title:",
        result_metadatas[index][
            "title"
        ]
    )


    print(
        "Category:",
        result_metadatas[index][
            "category"
        ]
    )


    print(
        "Distance:",
        result_distances[index]
    )


    print(
        "Text:"
    )


    print(
        result_documents[index]
    )
