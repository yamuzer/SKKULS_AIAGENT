import csv
from pathlib import Path
import chromadb
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"
CSV_PATH = BASE_DIR / "data" / "support_knowledge_72.csv"

CHROMA_PATH = BASE_DIR / "chroma_rag_threshold_data"
COLLECTION_NAME = "support_rag_threshold"

EMBEDDING_MODEL = "gemini-embedding-2"
GENEARTION_MODEL = "gemini-3.7-flash"
OUTPUT_DIMENSION = 768

CANDIDATE_K = 5
MAX_CONTEXT_DOCS = 3
MIN_SIMILARITY = 0.70


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

def load_row(csv_path: Path) -> list[dict]:

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


rows = load_row(CSV_PATH)
print_title('문의 데이터 확인')
print(f'문의 수:{len(rows)}')
print(f'첫 문의: {rows[0]}')


def to_bool(value: str) -> bool:
    return value.strip().lower() == 'true'


def embed_text(
    text: str,
) -> list[float]:

    result = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
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


def make_document(document: dict) -> str:

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
        document = make_document(row)
        embedding = embed_text(document)

        ids.append(row['doc_id'])
        documents.append(document)
        embeddings.append(embedding)
        metadatas.append(
            {
                'category': row['category'],
                'category_ko': row['category_ko'],
                'title': row['title'],
                'source': row['source'],
                'updated_at': row['updated_at'],
            }
        )

        print(f'{index:02d}/{len(rows)}')
        print(f'{row["doc_id"]} / {row["title"]} -> {len(embedding)}차원')


    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print('\n저장 완료')
    print(f'collection count: {collection.count()}')


prepare_collection()


def retrieve_candidates(question: str) -> dict:
    query_vector = embed_text(question)

    return collection.query(
        query_embeddings=[query_vector],
        n_results=CANDIDATE_K,
        include=[
            'documents',
            'metadatas',
            'distances'
        ]
    )


def convert_candidates(result: dict) -> list[dict]:

    candidates = []
    ids = result['ids'][0]

    for index in range(len(ids)):
        distance = float(result['distances'][0][index])
        similarity = 1.0 - distance

        candidates.append(
            {
                'id': ids[index],
                'document': result['documents'][0][index],
                'metadata': result['metadatas'][0][index],
                'distance': distance,
                'similarity': similarity
            }
        )

    return candidates


def filter_by_threshold(candidates: list[dict]) -> list[dict]:

    accepted = []

    for candidate in candidates:
        if candidate['similarity'] >= MIN_SIMILARITY:
            accepted.append(candidate)

    return accepted[:MAX_CONTEXT_DOCS]



def print_candidates(candidates: list[dict]) -> None:
    print_title('1. chromaDB 후보 Top - k')
    print(f'후보 수: {len(candidates)}')
    print(f'threshold: {MIN_SIMILARITY}')

    for rank, item in enumerate(candidates, start=1):
        passed = item['similarity'] >= MIN_SIMILARITY

        print(f'\n[{rank}위]')
        print(f'ID: {item["id"]}')
        print(f'title: {item["metadata"]["title"]}')
        print(f'distance: {round(item["distance"], 6)}')
        print(f'similarity: {round(item["similarity"], 6)}')
        print(f'threshold 통과 여부: {passed}')


def print_accepted(accepted: list[dict]) -> None:
    print_title('2. threshold 적용 후 Context 문서')
    if not accepted:
        print('사용할 수 있는 근거 문서가 없습니다.')
        return

    print(f'채택된 문서 수: {len(accepted)}')

    for rank, item in enumerate(accepted, start=1):
        print(
            f'\n[{rank}] {item["id"]} / {item["metadata"]["title"]} / '
            f'similarity: {item["similarity"]:.6f}'
        )



def build_context(accepted: list[dict]) -> str:

    parts = []

    for item in accepted:
        metadata = item['metadata']

        parts.append(
            f"[{item['id']}]\n"
            f"제목: {metadata['title']}\n"
            f"출처: {metadata['source']}\n"
            f"업데이트: {metadata['updated_at']}\n"
            f"검색 유사도: {item['similarity']:.4f}\n"
            f"내용: {item['document']}"
        )

    return '\n\n'.join(parts)


def generator_answer(
        question: str,
        context: str
) -> str:

    prompt = f"""
당신은 고객 지원 지식 문서를 근거로 답변하는 도우미입니다.

[규칙]
1. 반드시 [Context]에 있는 정보만 사용하세요.
2. Context에 없는 내용을 추가하거나 추측하지 마세요.
3. 서로 다른 문서 내용이 충돌하면 임의로 결정하지 말고 충돌 사실을 알려주세요.
4. 답변은 한국어로 간결하고 이해하기 쉽게 작성하세요.
5. 답변 마지막에는 실제로 사용한 문서 ID를 표시하세요.

형식:
근거 문서: [KB-001], [KB-002]

[Context]

{context}


[사용자 질문]

{question}


[답변]
"""

    response = gemini_client.models.generate_content(
        model=GENEARTION_MODEL,
        contents=prompt
    )

    return response.text or ""


def no_evidence_answer() -> str:
    return (
        '검색된 지식 문서 중 신뢰 기준을 만족하는 근거가 없습니다.\n'
        '현재 지식 베이스만으로 답변하지 않겠습니다.'
    )


def rag(question: str) -> None:
    raw_result = retrieve_candidates(question)
    candidates = convert_candidates(raw_result)

    print_candidates(candidates)

    accepted = filter_by_threshold(candidates)
    print_accepted(accepted)

    if not accepted:
        print_title('3. 최종 답변')
        print(no_evidence_answer)
        print('\nGemini Generation 호출: 하지 않음')
        return

    context = build_context(accepted)

    print_title('3. gemini context')
    print(context)

    answer = generator_answer(
        question=question,
        context=context
    )


    print_title('4. RAG 최종 답변')
    print(answer)



def run_cli() -> None:
    print_title('RAG Similarity Threshold')
    print(f'현재 threshold: {MIN_SIMILARITY}')
    print(f'후보 Top-K: {CANDIDATE_K}')
    print(f'최대 context 문서 수: {MAX_CONTEXT_DOCS}')
    print('\n 종료하려면 /exit')

    while True:
        print()
        question = input('질문 > ').strip()

        if question == '':
            continue

        if question == '/exit':
            print('프로그램을 종료합니다.')
            break

        rag(question)


if __name__ == "__main__":
    run_cli()