import os, json
import pandas as pd
from pathlib import Path
import chromadb
from typing import TypedDict, Literal
from dotenv import load_dotenv
import networkx as nx
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GRAPH_JSON_PATH = DATA_DIR / "knowledge_graph.json"
CHROMA_DIR = DATA_DIR / "chroma_hybrid_db"

ENV_PATH = BASE_DIR / "../.env"
load_dotenv(dotenv_path=ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        'GEMINI_API_KEY가 없습니다.'
    )

client = genai.Client(api_key=GEMINI_API_KEY)

GENERATION_MODEL = "gemini-3.7-flash"
EMBEDDING_MODEL = "gemini-embedding-2"

EMBEDDING_DIMESION = 768

with open(
    GRAPH_JSON_PATH,
    'r',
    encoding='utf-8'
) as file:
    graph_data = json.load(file)


graph = nx.MultiDiGraph()

for node in graph_data['nodes']:
    graph.add_node(
        node['id'],
        type=node.get('type', 'Other'),
        source_documents=node.get('source_documents', [])
    )

for relation in graph_data['relations']:
    graph.add_edge(
        relation['source'],
        relation['target'],
        key=relation['edge_id'],
        relation=relation['relation'],
        source_document=relation['source_document']
    )


chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

COLLECTION_NAME = 'hybrid_rag_documents'

try:
    collection = chroma_client.get_collection(
        name=COLLECTION_NAME
    )
except Exception as error:
    raise RuntimeError('hybrid collection을 찾지 못했습니다.')

if collection.count() == 0:
    raise RuntimeError('chromaDB에 저장된 문서가 없습니다.')


available_entities = list(graph.nodes())

available_relations = sorted(
    {
        data.get('relation', "")
        for source, target, edge_key, data in graph.edges(keys=True, data=True)
        if data.get('relation', '')
    }
)


class GraphQueryPlan(BaseModel):

    start_entities: list[str] = Field(
        description='Graph 검색을 시작할 Entity'
    )

    relation_path: list[str] = Field(
        description='질문의 답을 찾기 위해 순서대로 따라갈 Relation'
    )


def create_graph_query_plan(
        question: str
) -> GraphQueryPlan:

    entity_text = '\n'.join(
        f"-- {entity}"
        for entity in available_entities
    )

    relation_text = '\n'.join(
        f"- {relation}"
        for relation in available_relations
    )

    prompt = f"""
사용자의 질문을 Knowledge Graph 검색용 Graph Query Plan으로 변환하세요.


[사용 가능한 Entity]

{entity_text}


[사용 가능한 Relation]

{relation_text}


반환:

1. start_entities
Graph 탐색을 시작할 Entity

2. relation_path
질문의 답을 찾기 위해 순서대로 따라갈 Relation


예:

질문:

"철수가 근무하는 회사는 어디에 있어?"


Graph:

철수
-- WORK_AT -->
ABC 회사
-- LOCATED_IN -->
서울


결과:

start_entities:

[
    "철수"
]


relation_path

[
    "WORKS_AT",
    "LOCATED_IN"
]


[규칙]

1. Graph에 존재하는 Entity만 사용하세요.
2. Graph에 존재하는 Relation만 사용하세요.
3. relation_path의 순서는 중요합니다.
4. 필요없는 Relation은 추가하지 마세요.
5. 판단할 수 없다면 빈 리스트를 반환하세요.


[사용자 질문]

{question}
"""

    interation = client.interactions.create(
        model=GENERATION_MODEL,
        input=prompt,
        response_format={
            'type':'text',
            'mime_type': 'application/json',
            'schema': GraphQueryPlan.model_json_schema()
        }
    )

    result = GraphQueryPlan.model_validate_json(
        interation.output_text
    )

    valid_entities = []

    for entity in result.start_entities:
        if not graph.has_node(entity):
            continue

        if entity in valid_entities:
            continue

        valid_entities.append(entity)


    valid_relation_path = []

    for relation in result.relation_path:
        if relation not in available_relations:
            continue

        valid_relation_path.append(relation)


    return GraphQueryPlan(
        start_entities=valid_entities,
        relation_path=valid_relation_path
    )


def follow_relation(
        current_node: str,
        relation_name: str
):

    #outcoming
    
    results = []

    for source, target, edge_key, data in graph.out_edges(
        current_node, keys=True, data=True
    ):
        if data.get('relation') != relation_name:
            continue

        results.append(
            {
                'next_node': target,
                'edge': {
                    'edge_id': edge_key,
                    'source': source,
                    'relation': data.get('relation', ''),
                    'target': target,
                    'source_document': data.get('source_document', '')
                }
            }
        )


    #incoming

    for source, target, edge_key, data in graph.in_edges(
            current_node, keys=True, data=True
        ):
            if data.get('relation') != relation_name:
                continue

            results.append(
                        {
                            'next_node': source,
                            'edge': {
                                'edge_id': edge_key,
                                'source': source,
                                'relation': data.get('relation', ''),
                                'target': target,
                                'source_document': data.get('source_document', '')
                            }
                        }
                    )

    return results


def traverse_relation_path(
        start_entity:str,
        relation_path: list[str]
):

    frontier = [
        {
            'current_node': start_entity,
            'edges': []
        }
    ]

    for relation_name in relation_path:
        next_froniter = []

        for item in frontier:
            matches = follow_relation(
                item['current_node'],
                relation_name
            )

            for match in matches:
                next_froniter.append(
                    {
                        'current_node': match['next_node'],
                        'edges':(
                            item['edges'] + [match['edge']]
                        )
                    }
                )

        if not next_froniter:
            return []

        frontier = next_froniter


    paths = []

    for item in frontier:
        paths.append(
            {
                'start_entity': start_entity,
                'end_entity': item['current_node'],
                'edges': item['edges']
            }
        )

    return paths


def retrieve_graph_paths(
        start_entities: list[str],
        relation_path: list[str]
):

    all_paths = []

    for entity in start_entities:
        paths = traverse_relation_path(
            entity, relation_path
        )

        all_paths.extend(paths)

    return all_paths


# document id
# 철수 -- WORKS_AT --> ABC 회사
# source_document = DOC-001
# ABC 회사 -- LOCATED_IN --> 서울
# source_document = DOC-003
# [DOC-001, DOC-003]

def collect_graph_document_ids(
        graph_paths
) -> list[str]:

    document_ids = []

    for path in graph_paths:
        for edge in path['edges']:
            doc_id = edge.get('source_document', '')

            if not doc_id:
                continue

            if doc_id in document_ids:
                continue

            document_ids.append(doc_id)

    return document_ids



def retrieve_graph_documents(
        document_ids: list[str]
):

    if not document_ids:
        return []

    result = collection.get(
        ids=document_ids,
        include=[
            'documents',
            'metadatas'
        ]
    )  

    document_map = {}

    result_ids = result.get('ids', []) or []
    result_documents = result.get('documents', []) or []
    result_metadatas = result.get('metadatas', []) or []


    for index, doc_id in enumerate(result_ids):

        document_map[doc_id] = {
            'doc_id': doc_id,
            'text': result_documents[index],
            'metadata': result_metadatas[index],
            'distance': None,
            'retrieval_sources': ['graph']
        }


    documents = []

    for doc_id in document_ids:
        if doc_id in document_map:
            documents.append(document_map[doc_id])

    return documents



def prepare_vector_query(
        question:str
) -> str:

    return (
        "task: search result | "
        f"query: {question}"
    )


def create_query_embedding(
        question: str
) -> list[float]:

    query_text = prepare_vector_query(question)

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query_text,
        config=types.EmbedContentConfig(
                output_dimensionality=EMBEDDING_DIMESION
        )
    )

    if not result.embeddings:
        raise RuntimeError('query embedding 결과가 없습니다.')


    return list(result.embeddings[0].values)


def retrieve_vector_documents(
        question: str,
        top_k: int = 3
):

    query_embedding = create_query_embedding(question)

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(
            top_k,
            collection.count()
        ),
        include=[
            'documents',
            'metadatas',
            'distances'
        ]
    )

    ids = result['ids'][0]
    documents = result['documents'][0]
    metadatas = result['metadatas'][0]
    distances = result['distances'][0]


    results = []

    for index, doc_id in enumerate(ids):
        results.append(
            {
                'doc_id': doc_id,
                'text': documents[index],
                'metadata': metadatas[index],
                'distance': distances[index],
                'retrieval_sources': [
                    'vector'
                ],
                'vector_rank': index + 1
            }
        )

    return results


'''
evidence fusion


1. graph evidence
2. vector-only evidence

'''


def fuse_evidence(
        graph_documents,
        vector_documents
):

    fused = []
    document_map = {}

    for graph_rank, document in enumerate(
        graph_documents, start=1
    ):

        fusued_document = {
            'doc_id': document['doc_id'],
            'text': document['text'],
            'metadata': document['metadata'],
            'retrieval_sources':[
                'graph'
            ],
            'graph_rank': graph_rank,
            'vector_rank': None,
            'distance': None
        }

        fused.append(fusued_document)
        document_map[document['doc_id']] = fusued_document


    for document in vector_documents:
        doc_id = document['doc_id']

        if doc_id in document_map:
            existing = document_map[doc_id]

            if 'vector' not in existing['retrieval_sources']:
                existing['retrieval_sources'].append('vector')

            existing['vector_rank'] = document['vector_rank']       
            existing['distance'] = document['distance']

            continue


        fusued_document = {
            'doc_id': doc_id,
            'text': document['text'],
            'metadata': document['metadata'],
            'retrieval_sources':[
                'vector'
            ],
            'graph_rank': None,
            'vector_rank': document['vector_rank'],
            'distance': document['distance']
        }

        fused.append(fusued_document)

        document_map[doc_id] = fusued_document

    return fused


def build_graph_context(
        graph_paths
) -> str:

    if not graph_paths:

        return ''

    blocks = []

    for path_index, path in enumerate(graph_paths, start=1):

        lines = [
            f"[GRAPH PATH {path_index}]"
        ]

        for edge in path['edges']:
            lines.append(
                (
                    f"{edge['source']} -- {edge['relation']} --> {edge['target']} "
                    f"(출처: {edge['source_document']})"
                )
            )

        lines.append(
            (
                "최종 도착 Entity: "
                f"{path['end_entity']}"
            )
        )

        blocks.append('\n'.join(lines))

    return '\n\n'.join(blocks)



def build_fused_evidence_context(
        fused_documents
) -> str:

    if not fused_documents:
        return ''

    blocks = []

    for index, document in enumerate(fused_documents, start=1):

        source_text  = (
            ' + '.join(
                source.upper()
                for source in document['retrieval_sources']
            )
        )

        lines = [
            f"[EVIDENCE {index}]",
            (
                "문서 ID: "
                f"{document['doc_id']}"
            ),
            (
                "검색 출처: "
                f"{source_text}"
            )
        ]

        if document['graph_rank'] is not None:
            lines.append(
                (
                    'Graph Evidence: 순위: '
                    f"{document['graph_rank']}"
                )
            )

        if document['vector_rank'] is not None:
            lines.append(
                (
                    'Vector 검색 순위: '
                    f"{document['vector_rank']}"
                )
            )

        if document['distance'] is not None:
            lines.append(
                (
                    'Vector Distance: '
                    f"{document['distance']}"
                )
            )

        lines.append("원문: ")
        lines.append(document['text'])

        blocks.append('\n'.join(lines))


    return '\n\n'.join(blocks)


def generate_answer(
        question: str,
        graph_context: str,
        evidence_context: str
) -> str:

    if not graph_context and not evidence_context:
        return '질문과 관련된 근거를 찾지 못했습니다.'

    prompt = f"""
당신은 Knowledge Graph와 Vector Search를 함께 사용하는 Hybrid RAG 시스템입니다.

다음 두 정보를 사용하세요.

1. Graph Context
Entity 사이의 관계와 Multi-hop 구조를 보여줍니다.

2. Fused Evidence
Graph Retrieval와 Vector Retrieval을 통합한 실제 원문 근거입니다.


[중요 규칙]
1. 제공된 근거에서 확인 할 수 있는 사실만 사용하세요.
2. Graph Context는 관계를 파악하는데 사용하세요.
3. Fused Evidence의 실제 원문을 통해 사실을 확인하세요.
4. GRAPH + VECTOR 양쪽에서 검색된 문서는 강한 근거로 참고할 수 있습니다.
5. VECTOR에서만 검색된 문서는 질문과 실제로 관련 있는지 확인한 후 사용하세요.
6. VECTOR 검색 결과에 있다는 이유만으로 모든 문서를 답변에 사용하지 마세요.
7. GRAPH 정보와 원문이 충돌한다면 실제 원문을 우선하세요.
8. 검색 결과에 없는 사실을 추측하지 마세요.
9. 근거가 부족하면 "제공된 검색 결과만으로는 답을 할 수 없습니다."라고 답하세요.
10. 답변 마지막에는 실제로 사용한 문서 ID를 표시하세요.


[GRAPH CONTEXT]

{graph_context}


[FUSED_EVIDENCE]

{evidence_context}


[사용자 질문]

{question}
"""

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt
    )

    return response.text


def hybrid_rag(
        question: str,
        vector_top_k: int = 3
):

    print(f'\n사용자 질문: {question}')

    query_plan = create_graph_query_plan(question)

    print('='*70)
    print('\nStep 1 - graph query plan')
    print('='*70)

    print(f'start Entity: {query_plan.start_entities}')
    print(f'relation Path: {query_plan.relation_path}')


    graph_paths = retrieve_graph_paths(
        query_plan.start_entities,
        query_plan.relation_path
    )

    graph_context = build_graph_context(graph_paths)

    print()
    print('='*70)
    print('step 2 - graph retrieval')
    print('='*70)

    if graph_paths:
        for path_index, path in enumerate(graph_paths, start=1):
            print(f'\n[Path {path_index}]')

            for edge in path['edges']:
                print(
                    f"{edge['source']} -- {edge['relation']} --> {edge['target']} | "
                    f"{edge['source_document']}"
                )

    else:
        print('Graph 검색 결과 없음')


    graph_document_ids = collect_graph_document_ids(graph_paths)
    graph_docuemnts = retrieve_graph_documents(graph_document_ids)


    print()
    print('='*70)
    print('step 3 graph Evidence')
    print('='*70)

    for document in graph_docuemnts:
        print(f'[{document["doc_id"]}]')
        print(document['text'])
        print()



    vector_documents = retrieve_vector_documents(
        question,
        top_k=vector_top_k
    )

    print()
    print('='*70)
    print('step 4 vector Evidence')
    print('='*70)

    for document in vector_documents:
        print(f'[Vector Rank {document["vector_rank"]}]')
        print(f'문서 Id: {document["doc_id"]}')
        print(f"내용: {document['text']}")
        print()


    fused_documents = fuse_evidence(
        graph_docuemnts,
        vector_documents
    )

    evidence_context = build_fused_evidence_context(
        fused_documents
    )

    print()
    print('='*70)
    print('step 5 fused Evidence Context')
    print('='*70)
    print(
        evidence_context
        if evidence_context else 'Evidence 없음'
    )


    answer = generate_answer(
        question,
        graph_context,
        evidence_context
    )

    print()
    print('='*70)
    print('step 6 gemini answer')
    print('='*70)

    print(answer)


    return {
        'question': question,
        'query_plan': query_plan.model_dump(),
        'graph_paths': graph_paths,
        'graph_document_ids': graph_document_ids,
        'graph_documents': graph_docuemnts,
        'vector_documents': vector_documents,
        'fused_documents': fused_documents,
        'graph_context': graph_context,
        'evidence_context': evidence_context,
        'answer': answer
    }

question = '철수가 근무하는 회사는 어디에 있어?'

result = hybrid_rag(
    question,
    vector_top_k=3
)
