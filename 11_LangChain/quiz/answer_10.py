import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

import csv
from collections import defaultdict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

CSV_PATH = BASE_DIR / "data" / "smartfarm_operations_480.csv"
CHROMA_PATH = BASE_DIR / "chroma_smartfarm_review"
COLLECTION_NAME = "smartfarm_operations"
CHUNK_SIZE = 180
CHUNK_OVERLAP = 40

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2", api_key=api_key, output_dimensionality=768
)

def load_raw(path: Path) -> list[dict]:
    with path.open(mode="r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def row_to_document(row: dict) -> Document:
    return Document(
        id=row["record_key"],
        page_content=row["guide_text"],
        metadata={
            "record_key": row["record_key"], "topic_code": row["topic_code"],
            "topic_name": row["topic_name"], "subject": row["subject"],
            "risk_level": row["risk_level"], "equipment": row["equipment"],
            "season": row["season"],
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

chunk_ids = [
    f"{chunk.metadata['parent_record_key']}-K{chunk.metadata['chunk_index']:03d}"
    for chunk in chunk_documents
]

print("chunk_ids 개수 == chunk_documents 개수:", len(chunk_ids) == len(chunk_documents))
print("ID 중복 없음:", len(set(chunk_ids)) == len(chunk_ids))
print("\n앞 10개 ID")
for chunk_id in chunk_ids[:10]:
    print(chunk_id)
print("\n저장 경로:", CHROMA_PATH)
print("collection:", COLLECTION_NAME)
print("embedding 객체:", type(embeddings).__name__)
print("Chroma 클래스:", Chroma)
print("chunk_ids 준비 수:", len(chunk_ids))
print("\n실제 Chroma 생성/저장은 이번 복습 범위에서 수행하지 않습니다.")
