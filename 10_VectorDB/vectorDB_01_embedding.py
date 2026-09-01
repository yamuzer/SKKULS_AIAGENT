# csv문서를 gemini 임베딩 모델 기반 벡터문서 만들기
# 라이브러리가 토크나이징과 인덱싱을 자동으로 해줌
import csv
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
import math


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR /"../.env"
CSV_PATH = BASE_DIR / "data" / "knowledge_base.csv"

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

client = genai.Client(
    api_key=api_key
)

MODEL_NAME = "gemini-embedding-2"

#vector dimension
OUTPUT_DIMENSION = 768 # 최소값

def print_title(title:str):
    print('\n' + '-' * 80)
    print(title)
    print('-' * 80)
    print()


def load_document(csv_path: Path) -> list[dict]:

    with csv_path.open(
        mode='r',
        encoding='utf-8-sig',
        newline=''
    )as csv_file:

        return list(
            csv.DictReader(csv_file)
        )

documents = load_document(CSV_PATH)
print(f'사용할 문서 수: {len(documents)}')
print(f'첫 문서: {documents[0]}')


def embed_text(text: str) -> list[float]:

    result = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=OUTPUT_DIMENSION
        )
    )
    print()
    print(result, end='\n\n\n')
    return result.embeddings[0].values


# sample_text = (
#     '벡터 데이터베이스는 의미가 비슷한 문서를 검색하는데 사용된다.'
# )

# sample_vector = embed_text(sample_text)
# print_title(f'입력 문장: {sample_text}')
# print(f'dimension: {len(sample_vector)}')
# print('Vector 앞에서 부터 10개 만 출력')
# print(sample_vector[:10])
# print()


# 정형화된 규칙이 있을 경우
# def make_document_text(document: dict) -> str:
#     return (
#         f'{document['title']}. {document['content']}'
#     )


document_vectors = []

print_title('문서 embedding')

for index, document in enumerate(documents, start=1):

    # document_text  = make_document_text(document)
    document_text['contents'] = document.values()

    vector = embed_text(document_text)

    document_vectors.append(vector)

    print(
        f'{index:03d}/{len(documents)} '
        # f'{document['category']} / {document['title']} '
        f'-> {len(vector)}차원'
    )

print(f'\n전체 문서 vector 수: {len(document_vectors)}')
    




 # 위에서 만든 벡터 문서를 기반으로 질의 텍스트와 가장 가까운 5개의 임베딩 값 조회
def cosine_similarity(
    vector_a : list[float],
    vector_b : list[float]
) -> float:
    if len(vector_a) != len(vector_b):
        raise ValueError(
            '두 vector 차원이 다릅니다.'
        )

    dot_product = (
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(
            a * a 
            for a in vector_a
        )
    )

    magnitude_b = math.sqrt(
        sum(
            b * b 
            for b in vector_b
        )
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return (
        dot_product / (magnitude_a * magnitude_b)
    )

def semantic_search(
    query: str,
    top_k: int = 5
) -> list[dict]:
    query_vector = embed_text(query)

    results = []

    for ducument, document_vector in zip(documents, document_vectors):    
        similarity = cosine_similarity(
            query_vector,
            document_vector
        )
 
# 딕셔너리 언패킹해서 유사도 값 추가
        results.append(
            {
                **document,
                'similarity' : similarity
            }
        )

    results.sort(
        key=lambda item: item['similarity'],
        reverse=True
    )
    return results[:top_k]

def print_search_result(
    query: str,
    top_k : int = 5
) -> None:
    print_title(f'검색 질문: {query}')

    results = semantic_search(
        query=query,
        top_k=top_k
    )

    for rank, result in enumerate(results, start=1):
        print(f'\n{rank}위')
        # print(f'category: {result["category"]}')
        # print(f'title: {result["title"]}')
        print(f'similarity: {result["similarity"]}')
        print(f'contents: {result["contents"]}')




# print_search_result(
#     '데이터에 비어 있는 값이 있는데 없애거나 다른 값으로 채우고 싶어'
# )