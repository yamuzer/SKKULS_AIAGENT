import csv
from collections import defaultdict
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "smartfarm_operations_480.csv"
CHUNK_SIZE = 180
CHUNK_OVERLAP = 40

def load_raw(csv_path: Path) -> list[dict]:
    with csv_path.open(mode="r", encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))

def row_to_document(row: dict) -> Document:
    return Document(
        id=row["record_key"],
        page_content=row["guide_text"],
        metadata={
            "record_key": row["record_key"],
            "topic_code": row["topic_code"],
            "topic_name": row["topic_name"],
            "subject": row["subject"],
            "risk_level": row["risk_level"],
            "equipment": row["equipment"],
            "season": row["season"],
        },
    )

rows = load_raw(CSV_PATH)
documents = [row_to_document(row) for row in rows]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)
chunk_documents = splitter.split_documents(documents)

parent_counters = defaultdict(int)
for chunk in chunk_documents:
    parent_key = chunk.metadata["record_key"]
    parent_counters[parent_key] += 1
    chunk.metadata["parent_record_key"] = parent_key
    chunk.metadata["chunk_index"] = parent_counters[parent_key]

total_chunks_by_parent = defaultdict(int)
for chunk in chunk_documents:
    total_chunks_by_parent[chunk.metadata["parent_record_key"]] += 1
for chunk in chunk_documents:
    parent_key = chunk.metadata["parent_record_key"]
    chunk.metadata["total_chunks"] = total_chunks_by_parent[parent_key]

for chunk in chunk_documents[:12]:
    print()
    print(f"[원본문서] {chunk.metadata['parent_record_key']}")
    print(f"[chunk] {chunk.metadata['chunk_index']} / {chunk.metadata['total_chunks']}")
    print(f"[길이] {len(chunk.page_content)}")
    print(f"[본문] {chunk.page_content}")

lengths = [len(chunk.page_content) for chunk in chunk_documents]
print("\n전체 chunk 수:", len(chunk_documents))
print("평균 chunk 길이:", round(sum(lengths) / len(lengths), 2))
print("가장 긴 chunk 길이:", max(lengths))
