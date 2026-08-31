import os, csv
from collections import defaultdict
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
# pip install langchain-text-splitters

BASE_DIR = Path(__file__).resolve().parent

CSV_PATH = BASE_DIR / "data" / "support_documents_24.csv"

CHUNK_SIZE = 40
CHUNK_OVERLAP = 10

def print_title(title:str)-> None:
    print('\n'+'='*80)
    print(title)
    print('='*80)
    print()


# 딱 120에서 자르지 않고 문장이 자연스럽게 끝나는 위치에서 자름
splitter = RecursiveCharacterTextSplitter(
    chunk_size = CHUNK_SIZE,
    chunk_overlap = CHUNK_OVERLAP,
    separators=[ # 우선순위
        '\n\n',
        '\n',
        ' ',
        ''
    ],
    length_function=len
)

print_title('splitter')
print(type(splitter))

sample_text = (
    'Vector Database는 Embedding Vector 를 저장하고'
    '벡터 사이의 거리나 유사도를 이용해 의미가 비슷한 데이터를 찾는데 사용됩니다.'
    '일반적인 키워드 검색과 달리 문장이 정확히 같지 않아도 의미가 비슷하면 관련 문서를'
    '찾을 수 있습니다. RAG에서는 사용자의 질문과 관련된 문서를 검색하는 Retrieval의'
    '저장소로 자주 활용됩니다.'
)

text_chunks = splitter.split_text(sample_text)
print_title('splitter text')
print(f'생성 chunk 수 : {len(text_chunks)}')
for index, chunk in enumerate(text_chunks, start=1):
    print(f'\n[chunk {index}]')
    print(f'length: {len(chunk)}')
    print(chunk)

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
print(f'documents len: {len(documents)}')


chunk_documents = splitter.split_documents(documents)
print_title('split_documents')
print(f'chunk document len: {len(chunk_documents)}')
print()
print(chunk_documents[0])

for index, chunk in enumerate(chunk_documents[:8], start=1):
    print(f'\n[chunk {index}]')
    print(f'원본 doc_id: {chunk.metadata['doc_id']}')
    print(f'length: {len(chunk.page_content)}')
    print(f'제목 : {chunk.metadata['title']}')
    print(f'본문 : {chunk.page_content}')
    print(chunk)
print()

# chunk 원본 찾기. 설명 가능 한., 조회하기 위한. 추척하기 위한. 

# 존재하지 않는 키로 접근할 때 에러대신 기본값 0을 반환하는 특수 딕셔너리(에러방지, 자동초기화, 카운팅 편의성)
parent_counters = defaultdict(int) 

for chunk in chunk_documents:
    parent_id = chunk.metadata['doc_id']
    parent_counters[parent_id] += 1

    chunk.metadata['parent_doc_id'] = parent_id # 부모문서 ID기록
    chunk.metadata['chunk_index'] = parent_counters[parent_id] # 부모 내 순번

total_chunks_by_parent = defaultdict(int)

for chunk in chunk_documents:
    total_chunks_by_parent[chunk.metadata['parent_doc_id']] += 1

for chunk in chunk_documents:
    parent_id = chunk.metadata['parent_doc_id']
    chunk.metadata['total_chunks'] = total_chunks_by_parent[parent_id]

print_title('parent / chunk index')

for chunk in chunk_documents[:8]:
    print(
        f'{chunk.metadata["parent_doc_id"]}\n'
        f"{chunk.metadata['chunk_index']} / {chunk.metadata["total_chunks"]}"
    )
    print(chunk.page_content)