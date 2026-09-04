import os, json
import pandas as pd
from pathlib import Path
from typing import TypedDict, Literal
from dotenv import load_dotenv
import networkx as nx
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from langgraph.graph import START, END, StateGraph

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
JSON_PATH = DATA_DIR / "knowledge_multidigraph.json"
NODE_CSV_PATH = DATA_DIR / "nodes.csv"
RELATION_CSV_PATH = DATA_DIR / "relation.csv"


load_dotenv(dotenv_path=ENV_PATH)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

if not GEMINI_API_KEY:
    raise ValueError(
        'GEMINI_API_KEY가 없습니다.'
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)

class Entity(BaseModel):
    name: str = Field(
        description='Entity의 이름'
    )

    type: str = Field(
        description=(
            'Entity의 종류. '
        )
    )


class Relation(BaseModel):
    source: str = Field(
        description='관계의 출발 Entity'
    )

    relation: str = Field(
        description='관계 이름'
    )

    target: str = Field(
        description='관계의 도착 Entity'
    )


class KnowledgeGraphResult(BaseModel):

    entities : list[Entity]

    relations : list[Relation]


documents = [
    {
        'doc_id': 'DOC-001',
        'text': '철수는 ABC 회사에서 근무한다.'
    },
    {
        'doc_id': 'DOC-002',
        'text': '철수는 Python과 Pandas를 사용한다.'
    },
    {
        'doc_id': 'DOC-003',
        'text': 'ABC 회사는 서울에 위치한다.'
    },
    {
        'doc_id': 'DOC-004',
        'text': '영희는 ABC 회사의 대표다.'
    },
    {
        'doc_id': 'DOC-005',
        'text': '영희는 데이터 분석 분야를 담당하고 있다.'
    },
    {
        'doc_id': 'DOC-006',
        'text': '철수는 ABC 회사를 창립했다.'
    },
]

def extract_knowledge_grpah(
        text: str
) -> KnowledgeGraphResult:

    prompt = f"""
다음 문장에서 Knowledge Graph를 만들기 위한
Entity와 Relation을 추출하세요.

Entity type은 가능한 경우 아래 중 하나를 사용하세요.

- Person
- Company
- Technology
- City
- Field
- Product
- Organization
- Other


Relation은 다음 규칙을 따르세요.

1. 영문 대문자와 밑줄을 사용하세요.

예:
WORKS_AT
USES
LOCATED_IN
CEO_OF
WORKS_IN
USED_FOR
FOUNDED

2. 원문에서 확인 할 수 있는 사실만 사용하세요.
3. 같은 Entity는 중복 생성하지 마세요.
4. Relation의 source와 target 이름은 entities의 이름과 동일하게 사용하세요.
4. 같은 의미의 관계는 가능한 한 같은 Relation 이름으로 표현하세요.


원문:

{text}
"""

    interaction = client.interactions.create(
        model='gemini-3.7-flash',
        input=prompt,
        response_format={
            'type': 'text',
            'mime_type': 'application/json',
            'schema': KnowledgeGraphResult.model_json_schema()
        }
    )

    result = KnowledgeGraphResult.model_validate_json(interaction.output_text)

    return result


graph = nx.MultiDiGraph()


def add_entity(
        graph: nx.MultiDiGraph,
        entity: Entity,
        doc_id: str
):
    if graph.has_node(entity.name):
        node_data = graph.nodes[entity.name]

        source_documents = node_data.get('source_documents', [])

        if doc_id not in source_documents:
            source_documents.append(doc_id)

        node_data['source_documents'] = source_documents

        return


    graph.add_node(
        entity.name,
        type=entity.type,
        source_documents=[doc_id]
    )


for document in documents:

    doc_id = document['doc_id']
    text = document['text']

    print('\n')
    print('=' *70)
    print(f'분석 문서:{doc_id}')
    print(f'내용: {text}')
    print('=' *70)

    result = extract_knowledge_grpah(text)

    for entity in result.entities:
        add_entity(
            graph,
            entity,
            doc_id
        )


    #relation 누적

    for relation_index, relation in enumerate(result.relations, start=1):
        print(f'[Relation] {relation.source} -- {relation.relation} --> {relation.target}')

        edge_key = f"{doc_id}_REL-{relation_index:03d}"

        graph.add_edge(
            relation.source,
            relation.target,
            key=edge_key,
            relation=relation.relation,
            source_document=doc_id
        )


print('\n\n[최종 Entity]')
for node, data in graph.nodes(data=True):
    print(node, data)



print('\n\n[최종 Relation]')
for source, target, data in graph.edges(data=True):
    print(
        f'[Relation] {source} -- {data["relation"]} --> {target} | '
        f'출처: {data["source_document"]}'
        )
    

json_nodes = []

for node, data in graph.nodes(data=True):
    json_nodes.append(
        {
            'id': node,
            'type': data.get('type', 'other'),
            'source_documents': data.get('source_documents', [])
        }
    )


json_relations = []

for source, target, edge_key, data in graph.edges(keys=True, data=True):

    json_relations.append(
        {
            'edge_id': edge_key,
            'source': source,
            'relation': data.get('relation', ''),
            'target': target,
            'source_document': data.get('source_document', '')
        }
    )


json_data = {
    'nodes': json_nodes,
    'relations': json_relations
}

with open(
    JSON_PATH,
    'w',
    encoding='utf-8'
) as file:
    json.dump(
        json_data,
        file,
        ensure_ascii=False,
        indent=4
    )

print('json 저장 완료')