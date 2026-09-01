import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

import csv
import math
from collections import defaultdict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

CSV_PATH = BASE_DIR / "data" / "smartfarm_operations_480.csv"
CHUNK_SIZE = 180
CHUNK_OVERLAP = 40
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2", api_key=api_key, output_dimensionality=768
)

def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

def load_raw(path: Path) -> list[dict]:
    with path.open(mode="r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def row_to_document(row: dict) -> Document:
    return Document(
        id=row["record_key"],
        page_content=row["guide_text"],
        metadata={
            "record_key": row["record_key"], "area_code": row["area_code"],
            "topic_code": row["topic_code"], "topic_name": row["topic_name"],
            "subject": row["subject"], "risk_level": row["risk_level"],
            "equipment": row["equipment"], "season": row["season"],
        },
    )

rows = load_raw(CSV_PATH)
documents = [row_to_document(row) for row in rows]
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""], length_function=len
)
chunk_documents = splitter.split_documents(documents)
parent_counters = defaultdict(int)
for chunk in chunk_documents:
    parent_key = chunk.metadata["record_key"]
    parent_counters[parent_key] += 1
    chunk.metadata["parent_record_key"] = parent_key
    chunk.metadata["chunk_index"] = parent_counters[parent_key]

chunk_vectors = embeddings.embed_documents([c.page_content for c in chunk_documents])

default_question = (
    "여름철 A동에서 환기 후에도 잎에 물방울이 계속 맺혀 있어요. 관련 문서를 찾아주세요."
)
question = input("검색 질문을 입력하세요. Enter면 예시 질문 사용\n> ").strip() or default_question
qvec = embeddings.embed_query(question)

scored = []
for chunk, vector in zip(chunk_documents, chunk_vectors):
    scored.append((cosine_similarity(qvec, vector), chunk))
scored.sort(key=lambda item: item[0], reverse=True)

# 동일 parent는 최고 점수 chunk 하나만 유지
best_by_parent = {}
for score, chunk in scored:
    parent_key = chunk.metadata["parent_record_key"]
    if parent_key not in best_by_parent:
        best_by_parent[parent_key] = (score, chunk)
    if len(best_by_parent) >= 5:
        break

print("\n" + "=" * 80)
print("Top-5 검색 결과")
print("=" * 80)
for rank, (score, chunk) in enumerate(best_by_parent.values(), start=1):
    print(f"\n[{rank}위]")
    print("record_key :", chunk.metadata["record_key"])
    print("topic_name :", chunk.metadata["topic_name"])
    print("subject    :", chunk.metadata["subject"])
    print("risk_level :", chunk.metadata["risk_level"])
    print(f"similarity : {score:.6f}")
    print("content    :", chunk.page_content)
