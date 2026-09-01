# MMR : Maximal Marginal Relevance
# 질문과의 관련성을 유지하면서 검색결과끼리 너무 비슷한 문서만 반복되지 않도록 다양성을 고려하는 방법
# k : 선택할 문서 수
# fetch_k :참고할 문서 수
# lambda multiply : 검색된 문서 중 실제로 사용할 문서 수를 결정하는 가중치
# (다양성, 0~1, 0에 가까울수록 다른 문서, 1에 가까울수록 유사한 문서)

import os
from dotenv import load_dotenv
from pathlib import Path

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"
CSV_PATH = BASE_DIR / "data" / "support_documents_24.csv"

CHROMA_PATH = BASE_DIR / "chroma_langchain_data"
MARKER_PATH = CHROMA_PATH / 'created.marker'

COLLECTION_NAME = "support_documents"

CHUNK_SIZE = 40
CHUNK_OVERLAP = 10

load_dotenv(dotenv_path=ENV_PATH)
api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError('GEMINI_API_KEY를 읽을 수 없습니다.')

if not CHROMA_PATH.exists():
    raise FileNotFoundError('\nChromaDB를 찾을 수 없습니다.')

EMBEDDING_MODEL = (
    'gemini-embedding-2'
)

OUTPUT_DIMENSION = 768

embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=api_key,
    output_dimensionality=OUTPUT_DIMENSION
)

try:
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
        create_collection_if_not_exists=False
    )
except Exception as error:
    raise RuntimeError(
        'Chroma collection을 열 수 없습니다.'
    )

stored_data = vector_store.get(
    limit=5,
    include=[
        'documents',
        'metadatas'
    ]
)

stored_ids = stored_data.get('ids', [])

if not stored_ids:
    raise RuntimeError(
        'chorma collection을 열었지만 저장된 document가 없습니다.'
        )

def print_title(title: str) -> None:
    print('\n' + '=' * 80)
    print(title)
    print('='*80)
    print()

query = "결제나 구독 결제가 실패했을 때 어떤 항목들을 확인해야 하는지 알려주세요."

print_title(f'질문: \n{query}')
similarity_retriever = vector_store.as_retriever(
    search_type='similarity',
    search_kwargs={
        'k': 4
    }
)
 
print_title('similarity retriever 설정')
print(f'search_type: {similarity_retriever.search_type}')
print(f'\nsearch_kwargs: {similarity_retriever.search_kwargs}')

similarity_results = similarity_retriever.invoke(query)
print('\n\n 검색 결과')
for rank, document in enumerate(similarity_results, start=1):
    print_title(f'Rank {rank}')
    metadata = document.metadata
    print(f'[{rank}위]')
    print(f'문서 ID : {metadata.get("parent_doc_id", metadata.get("doc_id"))}')
    print(f'카테고리: {metadata.get("category_ko")}')
    print(f'본문: \n{document.page_content}')

mmr_retriever = vector_store.as_retriever(
    search_type='mmr',
    search_kwargs={
        'k': 4, # 선택할 문서수
        'fetch_k': 10, # 참고할 문서 수
        'lambda_mult': 0.3  # 유사한걸 덜 가져오겠다.
    }
)

print_title('MMR retriever 설정')
print(f'search_type: {mmr_retriever.search_type}')
print(f'\nsearch_kwargs: {mmr_retriever.search_kwargs}')

mmr_results = mmr_retriever.invoke(query)
print('\n\n 검색 결과')
for rank, document in enumerate(mmr_results, start=1):
    print_title(f'Rank {rank}')
    metadata = document.metadata
    print(f'[{rank}위]')
    print(f'문서 ID : {metadata.get("parent_doc_id", metadata.get("doc_id"))}')
    print(f'카테고리: {metadata.get("category_ko")}')
    print(f'본문: \n{document.page_content}')



filter_threshold_retriever = vector_store.as_retriever(
    search_type='similarity_score_threshold',
    search_kwargs={
        'k': 4,
        'score_threshold': 0.70,
        'filter':{
            'category': 'refund'
        }
    }
)