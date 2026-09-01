# Google Gemini의 최신 SDK(google-genai)를 활용해 고객 문의 데이터를 임베딩(768차원 Vector)하고, 이를 ChromaDB에 저장 및 유사도 검색(Semantic Search)하는 파이프라인

import csv
from pathlib import Path
import chromadb
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"
CSV_PATH = BASE_DIR / "data" / "support_tickets_50.csv"
CHROMA_PATH = BASE_DIR / "chroma_gemini_data"

COLLECTION_NAME = "gemini_support_ticket_collection"

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

# 데이터 임베딩 및 chromaDB 적재
def add_documents_if_needed() -> None:
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
                'title': row['title'],
            }
        )

        print(f'{index:02d}/{len(rows)}')
        print(f'{row["category_ko"]} / {row["title"]} -> {len(embedding)}차원')


    print_title('ChromaDB ADD')

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print('저장 완료')
    print(f'collection count: {collection.count()}')

        
add_documents_if_needed()


# 벡터 검색 및 카테고리 필터링
def semantic_search(
        query: str,
        top_k: int = 5,
        category: str | None = None
):

    query_vector = embed_text(query)

    if category is None:

        result = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=[
                'documents',
                'metadatas',
                'distances'
            ]
        )

    else:
        result = collection.query(
                    query_embeddings=[query_vector],
                    n_results=top_k,
                    where={
                        'category':category
                    },
                    include=[
                        'documents',
                        'metadatas',
                        'distances'
                    ]
                )

    return result



def print_search_result(
        query: str,
        top_k: int = 5,
        category: str | None = None
) -> None:
    
    print_title(f'검색 질문: {query}')
    print(f'category: {category}')
    print()

    result = semantic_search(
        query=query,
        top_k=top_k,
        category=category
    )

    for rank in range(len(result['ids'][0])):
        print(f'\n[{rank + 1}위]')

        print(f'id: {result["ids"][0][rank]}')

        print(f'category: {result["metadatas"][0][rank]["category"]}')

        print(f'title: {result["metadatas"][0][rank]["title"]}')

        print(f'distance: {round(result["distances"][0][rank], 6)}')

        print(f'document: {result["documents"][0][rank]}')


print_search_result(
    '카드에서 같은 금액이 두 번 빠져나간 것 같아요.'
)


print_search_result(
    '돈을 다시 돌려받고 싶은데 어떻게 해야 해?',
    category='refund'
)