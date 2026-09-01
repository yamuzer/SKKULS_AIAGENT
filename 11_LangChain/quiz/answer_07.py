import csv
from collections import Counter
from pathlib import Path
from langchain_core.documents import Document

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "smartfarm_operations_480.csv"

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

print("전체 Document 수:", len(documents))
for index, document in enumerate(documents[:3], start=1):
    print(f"\n[{index}]")
    print("id:", document.id)
    print("제목:", document.metadata["subject"])
    print("본문:", document.page_content[:120] + "...")

topic_counts = Counter(doc.metadata["topic_code"] for doc in documents)
print("\ntopic_code별 문서 수")
for topic_code, count in sorted(topic_counts.items()):
    print(f"{topic_code}: {count}")
