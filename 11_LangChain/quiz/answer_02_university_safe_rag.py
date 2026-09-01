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
from langchain_core.runnables import (
    RunnableLambda,
    RunnablePassthrough,
    RunnableBranch,
)


BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = (
    BASE_DIR
    / "data"
    / "university_policies_640.csv"
)

CHROMA_PATH = (
    BASE_DIR
    / "chroma_university_review"
)

MARKER_PATH = (
    CHROMA_PATH
    / "created.marker"
)

COLLECTION_NAME = (
    "university_policy_review"
)

CHUNK_SIZE = 300
CHUNK_OVERLAP = 60

TOP_K = 5
SCORE_THRESHOLD = 0.60
FILTER_POLICY_CATEGORY = "graduation"

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

        return list(csv.DictReader(csv_file))


def row_to_document(
    row: dict
) -> Document:

    return Document(
        id=row["policy_id"],
        page_content=row["policy_text"],
        metadata={
            "policy_id": row["policy_id"],
            "campus_code": row["campus_code"],
            "campus_name": row["campus_name"],
            "policy_category": row["policy_category"],
            "policy_category_ko": row["policy_category_ko"],
            "student_type": row["student_type"],
            "effective_year": int(
                row["effective_year"]
            ),
            "department_scope": row["department_scope"],
            "topic": row["topic"],
            "title": row["title"],
            "priority": row["priority"],
        },
    )


def create_chunks(
    documents: list[Document]
) -> list[Document]:

    splitter = (
        RecursiveCharacterTextSplitter(
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
    )

    chunks = splitter.split_documents(documents)

    parent_counter = defaultdict(int)

    for chunk in chunks:

        parent_id = chunk.metadata["policy_id"]

        parent_counter[parent_id] += 1

        chunk.metadata["parent_policy_id"] = parent_id

        chunk.metadata["chunk_index"] = parent_counter[parent_id]

    return chunks


embeddings = (
    GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=api_key,
        output_dimensionality=OUTPUT_DIMENSION,
    )
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

        stored_data = vector_store.get(
                limit=1,
                include=[
                    "metadatas"
                ],
        )

        if stored_data.get("ids"):

            return vector_store

    print_title("새 ChromaDB 생성")

    rows = load_raw(CSV_PATH)

    documents = [
        row_to_document(row)
        for row in rows
    ]

    chunks = create_chunks(documents)

    chunk_ids = []

    for chunk in chunks:

        chunk_id = (
            f"{chunk.metadata['parent_policy_id']}"
            f"-C{chunk.metadata['chunk_index']:03d}"
        )

        chunk_ids.append(chunk_id)

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

    print(f"원본 문서 수: {len(documents)}")

    print(f"저장 chunk 수: {len(chunks)}")

    return vector_store


vector_store = (
    prepare_vector_store()
)


retriever = (
    vector_store
    .as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": TOP_K,
            "score_threshold": SCORE_THRESHOLD,
            "filter": {
                "policy_category": FILTER_POLICY_CATEGORY
            },
        },
    )
)


def format_documents(
    documents: list[Document]
) -> str:

    context_blocks = []

    for index, document in enumerate(
        documents,
        start=1,
    ):

        metadata = (
            document.metadata
        )

        block = (
            f"[규정 {index}]\n"
            f"[policy_id: "
            f"{metadata.get('parent_policy_id', metadata.get('policy_id'))}]\n"
            f"[캠퍼스: {metadata.get('campus_name')}]\n"
            f"[학생 유형: {metadata.get('student_type')}]\n"
            f"[규정 분류: {metadata.get('policy_category_ko')}]\n"
            f"[제목: {metadata.get('title')}]\n"
            f"[내용: {document.page_content}]\n"
        )

        context_blocks.append(block)

    return "\n\n".join(context_blocks)


def prepare_prompt_input(
    data: dict
) -> dict:

    return {
        "question": data["question"],
        "context": format_documents(data["documents"]),
    }


def make_success_result(
    data: dict
) -> dict:

    return {
        "answer": data["answer"],
        "documents": data["documents"],
        "llm_called": True,
    }


def make_no_document_result(
    data: dict
) -> dict:

    return {
        "answer": (
            "관련 졸업 규정에서 "
            "근거를 찾지 못했습니다."
        ),
        "documents": [],
        "llm_called": False,
    }


model = ChatGoogleGenerativeAI(
    model="gemini-3.7-flash",
    api_key=api_key,
)


prompt = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "당신은 대학교 학사규정을 "
                    "근거로 답변하는 AI 도우미입니다.\n\n"
                    "반드시 제공된 Context만 근거로 답변하세요.\n"
                    "Context에 없는 규정을 추측해서 만들지 마세요.\n"
                    "캠퍼스나 학생 유형이 질문과 다르면 "
                    "그 차이를 명확하게 언급하세요.\n"
                    "답변은 한국어로 간결하게 작성하세요.\n\n"
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


answer_chain = (
    RunnableLambda(prepare_prompt_input)
    | prompt
    | model
    | StrOutputParser()
)


retrieval_chain = {
    "question": RunnablePassthrough(),
    "documents": retriever,
}


success_branch = (
    RunnablePassthrough.assign(answer=answer_chain)
    | RunnableLambda(make_success_result)
)


no_document_branch = RunnableLambda(make_no_document_result)


branch = RunnableBranch(
    (
        lambda data:
        len(
            data["documents"]
        ) > 0,
        success_branch,
    ),
    no_document_branch,
)


safe_rag_chain = (retrieval_chain | branch)


def print_result(
    question: str,
    result: dict,
) -> None:

    print_title("Safe RAG 결과")

    print("질문:")

    print(question)

    print(
        "\nLLM 호출 여부:",
        result["llm_called"],
    )

    print(
        "\n검색 문서 수:",
        len(result["documents"]),
    )

    print("\n답변:")

    print(result["answer"])

    if result["documents"]:

        print("\n검색 근거:")

        for document in result["documents"]:

            metadata = document.metadata

            print(
                "-",
                metadata.get("parent_policy_id", metadata.get("policy_id")),
                "/",
                metadata.get("title"),
            )


relevant_question = (
    "서울캠퍼스 학부생이 졸업학점을 모두 채웠지만 "
    "졸업논문 심사를 통과하지 못했다면 "
    "졸업할 수 있나요?"
)


irrelevant_question = (
    "화성 탐사선의 통신 안테나는 "
    "어떤 주파수를 사용하나요?"
)



relevant_result = (
    safe_rag_chain.invoke(relevant_question)
)


print_result(
    relevant_question,
    relevant_result,
)
print()


irrelevant_result = (
    safe_rag_chain.invoke(irrelevant_question)
)

print_result(
    irrelevant_question,
    irrelevant_result,
)
