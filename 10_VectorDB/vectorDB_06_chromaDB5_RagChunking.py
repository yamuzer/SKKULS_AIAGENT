import csv
from pathlib import Path
import chromadb
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"
CSV_PATH = BASE_DIR / "data" / "support_manual_18.csv"

CHROMA_PATH = BASE_DIR / "chroma_chunk_data"
COLLECTION_NAME = "support_manual_chunk"

EMBEDDING_MODEL = "gemini-embedding-2"
GENEARTION_MODEL = "gemini-3.7-flash"
OUTPUT_DIMENSION = 768

CHUNK_SIZE = 300
CHUNK_OVERLAP = 60
TOP_K = 4


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


source_document = load_row(CSV_PATH)


def split_text(
        text:str,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError(
            'chuck size는 1 이상이어야 합니다.'
        )

    if overlap < 0:
        raise ValueError(
            'overlap은 0 이상이여야 합니다.'
        )

    if overlap >= chunk_size:
        raise ValueError(
            'overlap은 chuck_size보다 작아야 합니다.'
        )


    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def create_chunk_records(
        documents: list[dict]
) -> list[dict]:

    records = []

    for document in documents:
        chunks = split_text(
            document['content']
        )

        total_chunks = len(chunks)

        for index, chunk_text in enumerate(chunks, start=1):
            records.append(
                {
                    "chunk_id": (
                        f"{document['doc_id']}-{index:03d}"
                    ),
                    'parent_doc_id': document['doc_id'],
                    'chunk_index': index,
                    'total_chunks': total_chunks,
                    'category': document['category'],
                    'category_ko': document['category_ko'],
                    'title': document['title'],
                    'source': document['source'],
                    'text': chunk_text,
                }
            )

    return records

chunk_records = create_chunk_records(source_document)

print_title('1. chunking 결과')
print(f'원본 문서 수: {len(source_document)}')
print(f'chunk 수: {len(chunk_records)}')

first_doc_id = source_document[0]['doc_id']

first_doc_chunks = [
    item
    for item in chunk_records
    if item['parent_doc_id'] == first_doc_id
]

print('\n첫 원문:')
print(f'{first_doc_id} / {source_document[0]["title"]}')

print(first_doc_chunks)



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
        f"제목: {document['title']}\n"
        f"내용: {document['text']}"
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
    
    if current_count == len(chunk_records):
        print('\n기존 chunck vector를 사용합니다.')
        return

    
    if current_count !=0:
            raise RuntimeError(
                '\nCollection에 일부 데이터만 존재합니다. 삭제 뒤 다시 실행하세요.'
            )
    
    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for index, row in enumerate(chunk_records, start=1):
        embedding_text = make_document(row)
        embedding = embed_text(embedding_text)

        ids.append(row['chunk_id'])
        documents.append(row['text'])
        embeddings.append(embedding)
        metadatas.append(
            {
                'parent_doc_id': row['parent_doc_id'],
                'chunk_index': row['chunk_index'],
                'total_chunks': row['total_chunks'],
                'category': row['category'],
                'category_ko': row['category_ko'],
                'title': row['title'],
                'source': row['source'],
            }
        )

        print(f'{index:02d}/{len(chunk_records)}')
        print(f'{row["chunk_id"]} / {row["title"]} -> {len(embedding)}차원')


    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print('\n저장 완료')
    print(f'collection count: {collection.count()}')


prepare_collection()


def retrieve_chunks(
        question: str,
        top_k: int = TOP_K
) -> dict:

    query_vector = embed_text(question)

    return collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=[
            'documents',
            'metadatas',
            'distances'
        ]
    )


def print_retireve_chunks(
        result: dict
) -> None:

    print_title('Retrieval - Chunk 검색 결과')

    ids = result['ids'][0]

    for rank in range(len(ids)):
        metadata = result['metadatas'][0][rank]
        distance = float(result['distances'][0][rank])
        similarity = 1.0 - distance
        print(f"\n[{rank + 1}위]")
        print(f"chunk id: {ids[rank]}")
        print(f"원본 id: {metadata['parent_doc_id']}")
        print(f"제목: {metadata['title']}")
        print(f"Similarity: {round(similarity, 6)}")
        print(f"chunk 내용:\n{result['documents'][0][rank]}")


def build_context(
        result: dict
) -> str:

    parts = []

    ids = result['ids'][0]

    for index in range(len(ids)):
        metadata = result['metadatas'][0][index]
        document = result['documents'][0][index]


        parts.append(
            (
                f"[Chunk: {ids[index]}]\n"
                f"원본 문서: {metadata['parent_doc_id']}\n"
                f"제목: {metadata['title']}\n"
                f"Chunk 위치: {metadata['chunk_index']}/{metadata['total_chunks']}\n"
                f"내용: {document}"
            )
        )

    return '\n\n'.join(parts)


def generate_answer(
        question: str,
        context: str
) -> str:

    prompt = f"""
당신은 고객지원 메뉴얼을 근거로 답변하는 도우미입니다.

[규칙]
1. 반드시 [Context]에 있는 정보만 사용하세요.
2. Context에 없는 내용을 추측하지 마세요.
3. 같은 원본 문서에서 나온 여러 Chunk가 있을 수 있습니다.
   중복되는 설명은 하나로 정리하세요.
4. 사용자가 바로 행동할 수 있도록 핵심 절차를 먼저 설명하세요.
5. 답변 마지막에는 사용한 Chunk ID를 표시하세요

형식:
근거 Chunk: [MAN-001-C001], [MAN-001-C002]


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


def rag(question: str) -> None:

    result = retrieve_chunks(question)

    print_retireve_chunks(result)

    context = build_context(result)

    print_title('Gemini context')
    print(context)

    answer = generate_answer(
        question=question,
        context=context
    )

    print_title('RAG 최종 답변')
    print(answer)


def run_cli() -> None:
    print_title('Chunk RAG')
    print(f'원본 문서 수 {len(source_document)}')
    print(f'전체 chunk 수: {len(chunk_records)}')
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

