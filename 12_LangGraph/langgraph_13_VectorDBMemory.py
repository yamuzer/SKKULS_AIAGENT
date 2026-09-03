import os, uuid, chromadb
from pathlib import Path
from typing import TypedDict, Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langgraph.graph import START, END, StateGraph

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

client = genai.Client(
    api_key=api_key
)

EMBEDDING_MODEL=('gemini-embedding-001')
EMBEDDING_DIM = 768

chroma_client = chromadb.PersistentClient(
    path='./chroma_memory_db'
)

collection = chroma_client.get_or_create_collection(
    name = 'semantic_memory'
)


class GraphState(TypedDict):
    action: Literal[
        'save',
        'search'
    ]
    user_id : str
    memory_text: str
    query: str
    retrieved_memory: str
    result: str


def create_embedding(text: str) -> list[float]:
    response = client.models.embed_content(
        model= EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIM
        )
    )

    embedding = response.embeddings[0].values
    
    return embedding


def save_memory_node(state: GraphState):
    print('\n[save_memory_node  실행]')

    user_id = state['user_id']
    memory_text = state['memory_text']
    print(f'user_id: {user_id}')
    print(f'저장 memory: {memory_text}')

    embedding = create_embedding(memory_text)

    memory_id = str(uuid.uuid4())

    collection.add(
        ids= [
            memory_id
        ],
        documents=[
            memory_text
        ],
        embeddings=[
            embedding
        ],
        metadatas=[
            {
                'user_id': user_id,
                'memory_type': 'semantic'
            }
        ]
    )
    return {
        'result': f'memory 저장 완료: {memory_text}'
    }

def search_memory_node(state: GraphState):
    print('\n[search_memory_node 실행]')
    user_id = state['user_id']
    query = state['query']
    print(f'검색 질문: {query}')

    query_embedding = create_embedding(query)
    results = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=3,
        where={
            'user_id': user_id
        }
    )

    documents = results['documents'][0]
    distances = results['distances'][0]

    print('\n검색 결과: ')

    for index, (document, distance) in enumerate(zip(documents, distances), start=1):
        print(f"{index}.")
        print(f'Memory: {document}')
        print(f'Distance: {distance}')
        print()

    if documents:
        best_memory = documents[0]
        return {
            'retrieved_memory': best_memory,
            'result': f'가장 관련있는 Memory: {best_memory}'
        }

    return {
        'retrieved_memory': '',
        'result': '관련 Memory를 찾지 못했습니다.'
    }

def route_action(state: GraphState):
    return state['action']

builder = StateGraph(GraphState)

builder.add_node(
    'save',
    save_memory_node
)

builder.add_node(
    'search',
    search_memory_node
)

builder.add_conditional_edges(
    START,
    route_action,
    {
        'save': 'save',
        'search': 'search'
    }
)

builder.add_edge(
    'save',
    END
)
builder.add_edge(
    'search',
    END
)

graph = builder.compile()

USER_ID = 'user_001'

# memory 저장
graph.invoke(
    {
        'action': 'save',
        'user_id': USER_ID,
        'memory_text':(
            '나는 Python으로 데이터 분석을 공부하고 있다.'
        ),
        'query': '',
        'retrived_memory': '',
        'result': ''
    }
)

graph.invoke(
    {
        'action': 'save',
        'user_id': USER_ID,
        'memory_text':(
            '나는 커피 중에서 에스프레소를 좋아한다.'
        ),
        'query': '',
        'retrived_memory': '',
        'result': ''
    }
)

graph.invoke(
    {
        'action': 'save',
        'user_id': USER_ID,
        'memory_text':(
            '나는 주말에 낚시나 게임을 하는 것을 좋아한다.'
        ),
        'query': '',
        'retrived_memory': '',
        'result': ''
    }
)

print('\nSemantic Memory 검색')

search_result = graph.invoke(
    {
        'action': 'search',
        'user_id': USER_ID,
        'memory_text': '',
        'query': (
            '내가 데이터를 다룰 때 공부하고 있는 프로그램 언어가 뭐였지?'
        ),
        'retrieved_memory': '',
        'result': ''
    }
)

print('\n 최종 검색 Memory ')
print(search_result['retrieved_memory'])