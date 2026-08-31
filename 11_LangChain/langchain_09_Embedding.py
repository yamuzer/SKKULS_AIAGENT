import os, csv, math
from collections import defaultdict
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"
CSV_PATH = BASE_DIR / "data" / "support_documents_24.csv"
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

chunk_texts = [
    chunk.page_content
    for chunk in chunk_documents
]

chunk_vecotrs= embeddings.embed_documents(chunk_texts)

print_title('전체 chunk embedding')
print(f'chunk 수: {len(chunk_texts)}')
print(f'embedding 수: {len(chunk_vecotrs)}')
print(f'첫 vector: {chunk_vecotrs[0][:10]}')
