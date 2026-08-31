import os, csv
from pathlib import Path
from langchain_core.documents import Document

BASE_DIR = Path(__file__).resolve().parent

CSV_PATH = BASE_DIR / "data" / "support_documents_24.csv"
'''
sample_document = Document(
    id = 'SAMPLE_001',
    page_content = (
        '비밀번호를 잊은 경우 가입 이메일을 이용해 비밀번호 재설정을 진행할 수 있습니다.'
    ),
    metadata={
        'category':'account',
        'title':'비밀번호 재설정',
        'source':'sample'
    }
)

print('\nLangchain Documnet')
print(sample_document)
print('\n page_content')
print(sample_document.page_content)
print(sample_document.metadata)
''' 

def load_raw(csv_path: Path) -> list[dict]:
    with csv_path.open(
        mode='r',
        encoding='utf-8-sig',
        newline='' 
    ) as csv_file:
        return list(
            csv.DictReader(csv_file)
        )

rows = load_raw(CSV_PATH)
# print(rows)

def row_to_document(row:dict)-> Document:
    return Document(
        id=row['doc_id'],
        page_content=row['content'],
        metadata={
            'doc_id':row['doc_id'],
            'category':row['category'],
            'category_ko':row['category_ko'],
            'title':row['title'],
            'source':row['source'],
            'priority':row['priority'],
        }
    )

documents = [
    row_to_document(row)
    for row in rows
]

print('\nDocument')
print(type(documents))
print(type(documents[0]))
print(documents)