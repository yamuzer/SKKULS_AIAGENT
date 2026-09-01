import csv
from pathlib import Path
import chromadb
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / "../.env"

CSV_PATH = BASE_DIR / "data" / "support_tickets_filter_50.csv"

CHROMA_PATH = BASE_DIR / "chroma_filter_data"

COLLECTION_NAME = "support_ticket_filter_collection"


load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY를 읽을 수 없습니다."
    )

if not CSV_PATH.exists():
    raise FileNotFoundError(
        f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}"
    )

gemini_client = genai.Client(
    api_key=api_key
)

MODEL_NAME = "gemini-embedding-2"

#vector dimension
OUTPUT_DIMENSION = 768

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


def to_bool(value: str) -> bool:
    return value.strip().lower() == 'true'


rows = load_document(CSV_PATH)
print_title('문의 데이터 확인')
print(f'문의 수:{len(rows)}')
print(f'첫 문의: {rows[0]}')


def embed_text(
    text: str,
) -> list[float]:

    result = gemini_client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=OUTPUT_DIMENSION
        )
    )

    vector = result.embeddings[0].values

    if (len(vector) != OUTPUT_DIMENSION):
        raise RuntimeError(
            'Embedding 차원이 예상고 다릅니다.'
        )

    return vector


def make_document_text(document: dict) -> str:

    return (
        f'{document['title']}. {document['content']}'
    )

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    configuration={
        'hnsw': {
            'space': 'cosine'
        }
    }
)


def prepare_collection() -> None:
    current_count = collection.count()
    
    if current_count == len(rows):
        print('\n이미 문서가 저장되어 있습니다.')
        return

    
    if current_count !=0:
            raise RuntimeError(
                '\nCollection에 일부 데이터만 존재합니다. 삭제 뒤 다시 실행하세요.'
            )
    
    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for index, row in enumerate(rows, start=1):
        document = make_document_text(row)
        embedding = embed_text(document)

        ids.append(row['ticket_id'])
        documents.append(document)
        embeddings.append(embedding)
        metadatas.append(
            {
                'category': row['category'],
                'category_ko': row['category_ko'],
                'priority': row['priority'],
                'channel': row['channel'],
                'region': row['region'],
                'customer_tier': row['customer_tier'],
                'year': int(row['year']),
                'response_hours': int(row['response_hours']),
                'severity': int(row['severity']),
                'resolved': to_bool(row['resolved']),
                'title': row['title'],
            }
        )

        print(f'{index:02d}/{len(rows)}')
        print(f'{row["category_ko"]} / {row["title"]} -> {len(embedding)}차원')


    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print('\n저장 완료')
    print(f'collection count: {collection.count()}')


prepare_collection()


def print_filter_records(
        title: str,
        where: dict,
        limit: int = 10
) -> None:

    print(f'title: {title}')
    print(f'where: {where}')


    result = collection.get(
        where=where,
        limit=limit,
        include=[
            'documents',
            'metadatas'
        ]
    )

    print(f'조회된 record 수: {len(result["ids"])}')

    for index, document_id in enumerate(result['ids']):

        metadata = result['metadatas'][index]

        print(f'\n[{index + 1}]')
        print(f'id: {document_id}')
        print(f'category: {metadata["category"]}')
        print(f'priority: {metadata["priority"]}')
        print(f'channel: {metadata["channel"]}')
        print(f'region: {metadata["region"]}')
        print(f'tier: {metadata["customer_tier"]}')
        print(f'response_hours: {metadata["response_hours"]}')
        print(f'severity: {metadata["severity"]}')
        print(f'resolved: {metadata["resolved"]}')
        print(f'title: {metadata["title"]}')

'''
print_filter_records(
    title='단일 조건 - 배송 문의',
    where={
        'category': 'delivery'
    }
)


print_filter_records(
    title='비교 조건 - 24시간 이상 걸린 문의',
    where={
        'response_hours': {
            '$gte':24
        }
    }
)



print_filter_records(
    title='AND 조건 - 환불 + high',
    where={
        '$and':[
            {
                'category': 'refund'
            },
            {
                'priority': 'high'
            }
        ]
    }
)



print_filter_records(
    title='OR 조건 - 환불 + high',
    where={
        '$or':[
            {
                'category': 'refund'
            },
            {
                'priority': 'high'
            }
        ]
    }
)

print_filter_records(
    title='IN - 결제 또는 환불',
    where={
        'category':{
            '$in': [
                'payment',
                'refund'
            ]
        }
    },
    limit=20
)
'''



print_filter_records(
    title='숫자 범위 - 12~24시간',
    where={
        '$and':[
            {
                'response_hours': {
                    '$gte': 12
                }
            },
            {
                'response_hours':{
                    '$lte': 24
                }
            }
        ]
    },
    limit=20
)
