# 벡터 데이터베이스에 데이터 삽입 및 조회(키조회, 벡터기반 검색), 메타데이터 수정

import csv
from pathlib import Path
import chromadb

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "support_tickets_50.csv"
CHROMA_PATH = BASE_DIR / "chroma_data"

COLLECTION_NAME = "support_ticket_collection"

def load_document(csv_path: Path) -> list[dict]:

    with csv_path.open(
        mode='r',
        encoding='utf-8-sig',
        newline=''
    )as csv_file:

        return list(
            csv.DictReader(csv_file)
        )

def print_title(title:str):
    print('\n' + '-' * 80)
    print(title)
    print('-' * 80)
    print()


rows = load_document(CSV_PATH)
print_title('문의 데이터 확인')
print(f'문의 수:{len(rows)}')
print(f'첫 문의: {rows[0]}')



client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    configuration={
        'hnsw': {
            'space': 'cosine'
        }
    }
)

'''
ids
documents
embeddings
metadatas
'''


ids = []

documents = []

embeddings = []

metadatas = []

for row in rows:
    ids.append(row['ticket_id'])

    documents.append(
        f'{row["title"]}. {row["content"]}'
    )

    embeddings.append(
        [
            float(row['v1']),
            float(row['v2']),
            float(row['v3']),
            float(row['v4']),
            float(row['v5']),
        ]
    )

    metadatas.append(
        {
            'category': row['category'],
            'category_ko': row['category_ko'],
            'priority': row['priority'],
            'channel': row['channel'],
            'title': row['title'],
        }
    )


current_count = collection.count()
print(f'현재 collection count: {current_count}')


if current_count == 0:
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print('50개 데이터 추가')
else:
    print('이미 저장된 데이터가 있으므로 다시 add하지 않습니다.')

print(f'추가 후 collection count: {collection.count()}')
print()





print_title('vectordb get')

get_result = collection.get(
    ids=[
        'TKT-001',
        'TKT-002',
        'TKT-003',
    ],

    include=[
        'documents',
        'metadatas',
        'embeddings'
    ]
)

print(f'ids: {get_result['ids']}')
print(f'\ndocuments: {get_result['documents']}')
print(f'\nmetadatas: {get_result['metadatas']}')
print(f'첫 embedding: {get_result['embeddings'][0]}')

payment_query_vector = [
    0.05,
    1.00,
    0.05,
    0.05,
    0.10
]

payment_result  = collection.query(
    query_embeddings=[payment_query_vector],
    n_results=5,
    include=[
        'documents',
        'metadatas',
        'distances'
    ]
)


for rank in range(len(payment_result['ids'][0])):
    print(f'\n[{rank+1}위]')
    print(f'id: {payment_result["ids"][0][rank]}')
    print(f'category: {payment_result["metadatas"][0][rank]["category"]}')
    print(f'title: {payment_result["metadatas"][0][rank]["title"]}')
    print(f'distance: {round(payment_result["distances"][0][rank], 6)}')


print()


temp_id = 'TKT-002'

'''
temp_existing = collection.get(
    ids=[temp_id]
)

if temp_existing['ids']:
    collection.delete(
        ids=[temp_id]
    )

print(f'삭제 후 collection count: {collection.count()}')
'''

collection.update(
    ids=[temp_id],
    metadatas=[
        {
            
            'category': 'payment',
            'category_ko': '결제',
            'priority': 'high',
            'channel': 'practice',
            'title': '임시 결제 문의'
        }
    ]
)

updated_data = collection.get(
    ids=[
        temp_id
    ]
)

print('\n수정된 후 metadata')
print(updated_data['metadatas'][0])

