import os
from pathlib import Path
from typing import TypedDict, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
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

class Entity(BaseModel):
    name: str = Field(
        description='Entity의 이름'
    )

    type: str = Field(
        description=(
            'Entity의 종류. '
            '예: Person, Company, Technology, City, Field'
        )
    )


class EntityExtractionResult(BaseModel):

    entities: list[Entity]


text = """
철수는 ABC 회사에서 근무하며 Python과 Pandas를 이용해 
데이터 분석 업무를 수행하고 있다.
"""

prompt = f"""
다음 문장에서 Knowledge Graph를 만들기 위해
중요한 Entity를 추출하세요.

Entity는 다음과 같은 종류를 우선 사용하세요.

- Person
- Company
- Technology
- City
- Field
- Product
- Organization
- Other


규칙:
1. 문장에 실제로 등장하거나 명확하게 의미가 있는 Entity만 추출하세요.
2. 같은 Entity를 중복해서 추출하지 마세요.
3. 일반적인 동사나 설명 문장은 Entity로 추출하지 마세요.
4. Entity 이름은 가능한 한 원문의 표현을 유지하세요.


원문:

{text}
"""

interaction = client.interactions.create(
    model='gemini-3.7-flash',
    input=prompt,
    response_format={
        'type':'text',
        'mime_type': 'application/json',
        'schema': EntityExtractionResult.model_json_schema()
    }
)

result = EntityExtractionResult.model_validate_json(interaction.output_text)

print('\n[Entity Extraction Result]')

for entity in result.entities:
    print(f'이름: {entity.name}')
    print(f'종류: {entity.type}')
    print()

print()

print(interaction.output_text)