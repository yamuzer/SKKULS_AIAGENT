import os, csv, math
from collections import defaultdict
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"
CSV_PATH = BASE_DIR / "data" / "support_documents_24.csv"

CHROMA_PATH = BASE_DIR / "chroma_langchain_data"
MARKER_PATH = CHROMA_PATH / 'created.marker'
# Marker의 의미: "이 데이터베이스는 이미 완전히 생성 및 저장이 완료되었으니, API를 다시 호출하지 말고 로컬 DB를 불러와라"라고 프로그램에 알려주는 확인용 징표입니다.
'''
1. Marker의 주요 역할
중복 생성 방지 (비용/시간 절약):
Chroma.from_documents()를 호출하면 텍스트를 Google API를 통해 임베딩(Vector 변환)하는 과정이 일어납니다. 매번 프로그램을 실행할 때마다 이 작업을 반복하면 API 호출 비용이 발생하고 실행 시간이 길어집니다.

캐싱 및 로딩 분기 처리:

최초 실행 시 (Marker 파일 없음): 문서 임베딩 및 Chroma DB 생성 후 created.marker 텍스트 파일을 새로 만들어 둡니다.

재실행 시 (Marker 파일 있음): DB를 새로 만들지 않고, 이미 생성되어 있는 Chroma DB 폴더(CHROMA_PATH)를 그대로 로드하여 로컬에서 즉시 검색을 시작합니다.

'''
COLLECTION_NAME = "support_documents"

CHUNK_SIZE = 40
CHUNK_OVERLAP = 10

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

EMBEDDING_MODEL=('gemini-embedding-2')

OUTPUT_DIMENSION = 768

def print_title(title:str)-> None:
    print('\n'+'='*80)
    print(title)
    print('='*80)
    print()

embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=api_key,
    output_dimensionality=OUTPUT_DIMENSION
)


query = '환불 완료인데 카드에 돈이 아직 안들어왔어요.'
query_vector = embeddings.embed_query(query)
print_title('embedding query')
print(f'query: {query}')
print(query_vector[:5])
print()

sample_texts = [
    (
        '환불 승인이 완료된 뒤 실제 카드나 계좌에 반영되기까지'
        '금융기관 처리 시간이 추가로 필요할 수 있다.'
    ),
    (
        '배송 완료로 표시되지만 상품이 없다면'
        '가족 수령 여부와 보관 장소를 확인한다.'
    ),
    (
        '앱이 실행 직후 강제 종료되면'
        '업데이트와 기기 재시작을 먼저 확인한다.'
    )
]
# 랭체인 크로마 라이브러리안의 임베딩 객체를 사용해본 것
# 랭체인 -> 임베일 -> 크로마db 순으로
# 쿼리, 도큐먼트 모두 벡터로 미리 변환하지 않고, 원본 그대로 넣어도 됨
document_vectors = embeddings.embed_documents(sample_texts)
print_title('embed documents')

print(f'입력 문서 수: {len(sample_texts)}')
print(f'verctor 문서 수 : {len(document_vectors)}')

for index, vector in enumerate(document_vectors, start=1):
    print(f'\nDocument {index}')
    print(f'vector: {vector[:5]}')


def cosine_similarity(
    vector_a : list[float],
    vector_b : list[float]
) -> float:
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return (dot_product / (norm_a * norm_b))

similarity_results = []

for text, vector in zip(sample_texts, document_vectors):
    similarity = cosine_similarity(query_vector, vector)
    similarity_results.append(
        (similarity, text)
    )
similarity_results.sort(
    key=lambda item: item[0],
    reverse=True
)

for rank, (similarity, text) in enumerate(similarity_results, start=1):
    print(f'\n{rank}위')
    print(f'similarity: {round(similarity, 6)}')
    print(text)


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

sample_text = (
    'Vector Database는 Embedding Vector 를 저장하고'
    '벡터 사이의 거리나 유사도를 이용해 의미가 비슷한 데이터를 찾는데 사용됩니다.'
    '일반적인 키워드 검색과 달리 문장이 정확히 같지 않아도 의미가 비슷하면 관련 문서를'
    '찾을 수 있습니다. RAG에서는 사용자의 질문과 관련된 문서를 검색하는 Retrieval의'
    '저장소로 자주 활용됩니다.'
)

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

chunk_documents = splitter.split_documents(documents)

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

chunk_ids = []
for chunk in chunk_documents:
    chunk_id = (
        f'{chunk.metadata['parent_doc_id']}-c{chunk.metadata['chunk_index']:03d}'
    )
    chunk_ids.append(chunk_id)


# 임베딩 객체와 청크 데이터가 직접 적재됨. 
def prepare_vector_store() -> Chroma:
    if not MARKER_PATH.exists():
        print('\n새 vector store를 생성합니다.')
        CHROMA_PATH.mkdir(parents=True, exist_ok = True)

        vector_store = Chroma.from_documents(
            documents=chunk_documents,
            embedding=embeddings,
            ids=chunk_ids,
            collection_name=COLLECTION_NAME,
            persist_directory=str(CHROMA_PATH)
        )

        MARKER_PATH.write_text(
            (
                f'collection={COLLECTION_NAME}\n'
                f'chunks={len(chunk_documents)}\n'
            ),
            encoding='utf-8'
        )

        print('\nVector Store 생성 완료')

        return vector_store
    
    print('\n기존 Vector store를 다시 엽니다.')

    vector_store = Chroma(  # 랭체인 크로마
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings, # 임베딩객체내장
        persist_directory=CHROMA_PATH
    )
    return vector_store

vector_store = prepare_vector_store()

print(f'\nvector store type: {type(vector_store)}')

query = "환불 완료인데 카드에 돈이 아직 안들어왔어요."

print_title('query search with score')
print(f'query: {query}')

scored_results = vector_store.similarity_search_with_score(
    query= query,
    k=4
)

print(f'\n검색 결과 수: {len(scored_results)}')
print(scored_results)
print()

for rank, (document, score) in enumerate(scored_results, start=1):
    print(f'[{rank}위]')
    print(f'원본 문서 id {document.metadata["parent_doc_id"]}')
    print(f'distance score: {round(float(score), 6)}')
    print(f'제목: {document.metadata["title"]}')
    print(f'본문: {document.page_content}')