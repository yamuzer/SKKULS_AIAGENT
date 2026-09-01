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
QUESTION_PATH = BASE_DIR / "data" / "retrieval_questions_72.csv"
CHUNK_SIZE = 180
CHUNK_OVERLAP = 40
EMBEDDING_MODEL = "gemini-embedding-2"
OUTPUT_DIMENSION = 768

embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL, api_key=api_key, output_dimensionality=OUTPUT_DIMENSION
)

def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def load_csv(path: Path) -> list[dict]:
    with path.open(mode="r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

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

# Part A
query = "저울 숫자가 작업 중 계속 틀어져요. 무엇을 확인해야 하나요?"
sample_texts = [
    "전자저울 숫자가 계속 달라지면 영점을 다시 맞추고 저울 아래 이물질과 수평 상태를 확인한다.",
    "저온창고 습도가 높으면 문 개방 시간과 제습기 동작 상태를 확인한다.",
    "관수 펌프 압력이 낮으면 흡입부 막힘과 필터 오염 여부를 확인한다.",
    "네트워크 지연이 반복되면 게이트웨이 연결 상태와 통신 지연 시간을 확인한다.",
]
query_vector = embeddings.embed_query(query)
document_vectors = embeddings.embed_documents(sample_texts)
results = []
for text, vector in zip(sample_texts, document_vectors):
    results.append((cosine_similarity(query_vector, vector), text))
results.sort(key=lambda item: item[0], reverse=True)
print("=" * 80)
print("Part A")
print("=" * 80)
for rank, (score, text) in enumerate(results, start=1):
    print(f"\n[{rank}위] {score:.6f}")
    print(text)

# Part B
rows = load_csv(CSV_PATH)
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
chunk_texts = [chunk.page_content for chunk in chunk_documents]
chunk_vectors = embeddings.embed_documents(chunk_texts)
print("\n" + "=" * 80)
print("Part B")
print("=" * 80)
print("chunk 수:", len(chunk_documents))
print("embedding 수:", len(chunk_vectors))
print("개수 일치:", len(chunk_documents) == len(chunk_vectors))
print("첫 vector 앞 10개:", chunk_vectors[0][:10])
print("vector 차원:", len(chunk_vectors[0]))

# Part C
question_rows = load_csv(QUESTION_PATH)[:10]
correct = 0
print("\n" + "=" * 80)
print("Part C")
print("=" * 80)
for qrow in question_rows:
    qvec = embeddings.embed_query(qrow["question"])
    scored = []
    for chunk, vector in zip(chunk_documents, chunk_vectors):
        scored.append((cosine_similarity(qvec, vector), chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    top3 = scored[:3]
    top1_code = top3[0][1].metadata["topic_code"]
    ok = top1_code == qrow["expected_topic_code"]
    correct += int(ok)
    print("\n" + "-" * 80)
    print(qrow["query_id"], qrow["question"])
    print("expected:", qrow["expected_topic_code"])
    for rank, (score, chunk) in enumerate(top3, start=1):
        print(f"  [{rank}] {chunk.metadata['topic_code']} | {chunk.metadata['record_key']} | {score:.6f}")
        print("     ", chunk.metadata["subject"])
    print("Top-1 정답 여부:", ok)
accuracy = correct / len(question_rows) * 100 if question_rows else 0
print(f"\nTop-1 주제 정확도: {correct}/{len(question_rows)} ({accuracy:.1f}%)")
