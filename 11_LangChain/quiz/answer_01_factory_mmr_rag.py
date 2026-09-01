import os
import csv
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI,
)
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough


BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = (
    BASE_DIR
    / "data"
    / "factory_maintenance_720.csv"
)

CHROMA_PATH = (
    BASE_DIR
    / "chroma_factory_review"
)

MARKER_PATH = (
    CHROMA_PATH
    / "created.marker"
)

COLLECTION_NAME = (
    "factory_maintenance_review"
)

CHUNK_SIZE = 260
CHUNK_OVERLAP = 50

EMBEDDING_MODEL = "gemini-embedding-2"
OUTPUT_DIMENSION = 768

load_dotenv(BASE_DIR / ".env")

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY를 읽을 수 없습니다."
    )


def print_title(
    title: str
) -> None:

    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print()


def load_raw(
    csv_path: Path
) -> list[dict]:

    with csv_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        return list(
            csv.DictReader(csv_file)
        )


def row_to_document(
    row: dict
) -> Document:

    return Document(
        id=row["manual_id"],
        page_content=row["manual_text"],
        metadata={
            "manual_id": row["manual_id"],
            "zone_code": row["zone_code"],
            "equipment_code": row["equipment_code"],
            "equipment_name": row["equipment_name"],
            "symptom_code": row["symptom_code"],
            "symptom_name": row["symptom_name"],
            "cause_code": row["cause_code"],
            "cause_name": row["cause_name"],
            "severity": row["severity"],
            "title": row["title"],
        },
    )


def create_chunk_documents(
    documents: list[Document]
) -> list[Document]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
        length_function=len,
    )

    chunks = splitter.split_documents(
        documents
    )

    parent_counter = defaultdict(int)

    for chunk in chunks:

        parent_id = chunk.metadata["manual_id"]

        parent_counter[parent_id] += 1

        chunk.metadata["parent_manual_id"] = parent_id

        chunk.metadata["chunk_index"] = parent_counter[parent_id]

    total_counter = defaultdict(int)

    for chunk in chunks:

        parent_id = (
            chunk
            .metadata[
                "parent_manual_id"
            ]
        )

        total_counter[parent_id] += 1

    for chunk in chunks:

        parent_id = (
            chunk
            .metadata[
                "parent_manual_id"
            ]
        )

        chunk.metadata["total_chunks"] = total_counter[parent_id]

    return chunks


embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=api_key,
    output_dimensionality=OUTPUT_DIMENSION,
)


def prepare_vector_store() -> Chroma:

    if (
        CHROMA_PATH.exists()
        and MARKER_PATH.exists()
    ):

        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=CHROMA_PATH,
            create_collection_if_not_exists=False,
        )

        stored = vector_store.get(
            limit=1,
            include=["metadatas"],
        )

        if stored.get("ids"):
            return vector_store

    print_title(
        "새 ChromaDB 생성"
    )

    rows = load_raw(
        CSV_PATH
    )

    documents = [
        row_to_document(row)
        for row in rows
    ]

    chunks = create_chunk_documents(
        documents
    )

    chunk_ids = []

    for chunk in chunks:

        chunk_id = (
            f"{chunk.metadata['parent_manual_id']}"
            f"-C{chunk.metadata['chunk_index']:03d}"
        )

        chunk_ids.append(
            chunk_id
        )

    CHROMA_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )

    vector_store.add_documents(
        documents=chunks,
        ids=chunk_ids,
    )

    MARKER_PATH.write_text(
        "created",
        encoding="utf-8",
    )

    print(
        f"원본 문서 수: {len(documents)}"
    )

    print(
        f"저장 chunk 수: {len(chunks)}"
    )

    return vector_store


vector_store = (
    prepare_vector_store()
)


query = (
    "컨베이어나 구동 모터에서 열이 올라가고 "
    "진동과 소음도 같이 발생합니다. "
    "한 가지 원인만 말하지 말고 어떤 가능성을 "
    "점검해야 하는지 찾아주세요."
)


similarity_retriever = (
    vector_store
    .as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 5,
        },
    )
)


mmr_retriever = (
    vector_store
    .as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "fetch_k": 20,
            "lambda_mult": 0.35,
        },
    )
)


def print_search_result(
    title: str,
    documents: list[Document],
) -> None:

    print_title(title)

    cause_codes = set()

    for rank, document in enumerate(
        documents,
        start=1,
    ):

        metadata = (
            document.metadata
        )

        cause_codes.add(
            metadata.get(
                "cause_code"
            )
        )

        print(
            f"[{rank}위]"
        )

        print(
            "manual_id:",
            metadata.get("parent_manual_id",  metadata.get("manual_id"),
            ),
        )

        print(
            "설비:",
            metadata.get("equipment_name"),
        )

        print(
            "증상:",
            metadata.get("symptom_name"),
        )

        print(
            "원인:",
            metadata.get("cause_name"),
        )

        print(
            document.page_content[:180]
        )

        print()

    print(
        "서로 다른 cause_code 수:",
        len(cause_codes),
    )


similarity_results = (
    similarity_retriever
    .invoke(query)
)

mmr_results = (
    mmr_retriever
    .invoke(query)
)

print_search_result(
    "Similarity 검색",
    similarity_results,
)

print_search_result(
    "MMR 검색",
    mmr_results,
)


def format_documents(
    documents: list[Document]
) -> str:

    blocks = []

    for index, document in enumerate(
        documents,
        start=1,
    ):

        metadata = (
            document.metadata
        )

        block = (
            f"[문서 {index}]\n"
            f"[manual_id: "
            f"{metadata.get('parent_manual_id', metadata.get('manual_id'))}]\n"
            f"[설비: {metadata.get('equipment_name')}]\n"
            f"[증상: {metadata.get('symptom_name')}]\n"
            f"[원인: {metadata.get('cause_name')}]\n"
            f"[위험도: {metadata.get('severity')}]\n"
            f"[제목: {metadata.get('title')}]\n"
            f"[내용: {document.page_content}]\n"
        )

        blocks.append(
            block
        )

    return "\n\n".join(
        blocks
    )


format_runnable = (
    RunnableLambda(
        format_documents
    )
)

question_passthrough = (
    RunnablePassthrough()
)


model = ChatGoogleGenerativeAI(
    model="gemini-3.7-flash",
    api_key=api_key,
)


prompt = (
    ChatPromptTemplate
    .from_messages(
        [
            (
                "system",
                (
                    "당신은 스마트팩토리 설비 유지보수 "
                    "지식 문서를 기반으로 답변하는 AI입니다.\n\n"
                    "반드시 제공된 Context만 근거로 답변하세요.\n"
                    "Context에 없는 고장 원인이나 조치 방법을 "
                    "추측해서 추가하지 마세요.\n"
                    "가능하면 서로 다른 원인을 구분해서 설명하세요.\n\n"
                    "답변 형식:\n"
                    "1. 우선 점검 원인\n"
                    "2. 확인 항목\n"
                    "3. 안전상 주의사항\n\n"
                    "[Context]\n"
                    "{context}"
                ),
            ),
            (
                "human",
                "{question}",
            ),
        ]
    )
)


rag_input_chain = {
    "context": (
        mmr_retriever
        | format_runnable
    ),
    "question": (
        question_passthrough
    ),
}


rag_chain = (
    rag_input_chain
    | prompt
    | model
    | StrOutputParser()
)


answer = rag_chain.invoke(
    query
)


print_title(
    "최종 RAG 답변"
)

print(
    "질문:"
)

print(query)

print("\n답변:")

print(answer)

print(
    "\n검색 문서 수:",
    len(mmr_results),
)

print("\n검색 근거:")

for document in mmr_results:

    metadata = document.metadata

    print(
        "-",
        metadata.get("parent_manual_id", metadata.get("manual_id")),
        "/",
        metadata.get("equipment_name"),
        "/",
        metadata.get("cause_name"),
    )
