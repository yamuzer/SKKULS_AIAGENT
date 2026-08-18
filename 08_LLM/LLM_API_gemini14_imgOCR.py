import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    ValidationError
)



BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / '.env'
IMAGE_PATH = BASE_DIR / 'data' / 'nutrition_label_basmati.jpg'

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError('GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.')


client = genai.Client(api_key=api_key)


def print_title(title: str) -> None:
    print('='*100)
    print(f'{title}')
    print('='*100)
    print()


upload_file = client.files.upload(file=str(IMAGE_PATH))

file_info = client.files.get(name=upload_file.name)
#print(file_info)



class NutritionLabelRaw(BaseModel):
    product_name: str | None = Field(
        description="이미지에서 직접 읽을 수 있는 상품명. 상품명이 보이지 않으면 null"
    )

    serving_basis: str | None = Field(
            description=(
            "영양 정보의 기준 단위."
            "예: PER 100g SERVING"
            )

    )

    energy_kj: str | None = Field(
            description=(
                "Energy 값을 숫자 문자열로 기록."
                "예: 1480."
                "읽을 수 없으면 null"
            )
        )

    calories_kcal: str | None = Field(
        description=(
            "Calories 값을 숫자 문자열로 기록. "
            "예: 350. "
            "읽을 수 없으면 null"
        )
    )

    protein_g: str | None = Field(
        description=(
            "Protein 값을 숫자 문자열로 기록. "
            "예: 9"
        )
    )

    carbohydrate_g: str | None = Field(
        description=(
            "Carbohydrate 값을 "
            "숫자 문자열로 기록"
        )
    )

    sugars_g: str | None = Field(
        description=(
            "Sugars 값을 "
            "숫자 문자열로 기록"
        )
    )

    fat_g: str | None = Field(
        description=(
            "Fat 값을 "
            "숫자 문자열로 기록"
        )
    )

    saturates_g: str | None = Field(
        description=(
            "Saturates 값을 "
            "숫자 문자열로 기록"
        )
    )

    fibre_g: str | None = Field(
        description=(
            "Fibre 값을 "
            "숫자 문자열로 기록"
        )
    )

    sodium_text: str | None = Field(
        description=(
            "Sodium 값은 이미지에 표시된 "
            "원래 표현을 그대로 기록. "
            "예: Trace g"
        )
    )

    extraction_confidence: Literal[
        "높음",
        "보통",
        "낮음",
    ] = Field(
        description=(
            "이미지 전체 판독 결과의 신뢰도"
        )
    )

    unreadable_or_missing_fields: list[str] = Field(
        description=(
            "이미지에서 읽을 수 없거나 "
            "존재하지 않는 필드 이름 목록"
        )
    )


class NutritionLabelResult(BaseModel):
    product_name: str | None 

    serving_basis: str | None 

    energy_kj: int | None

    calories_kcal: int | None
    
    protein_g: float | None

    carbohydrate_g: float | None

    sugars_g: float | None

    fat_g: float | None

    saturates_g: float | None

    fibre_g: float | None

    sodium_text: str | None

    extraction_confidence: Literal[
        "높음",
        "보통",
        "낮음",
    ]
    unreadable_or_missing_fields: list[str]



def to_int(value: str | None) -> int | None:
    if value is None:
        return None

    value = value.strip().replace(",", "")

    if not value:
        return None

    try:
        return int(float(value))
    except ValueError:
        return None


def to_float(value: str | None) -> float | None:
    if value is None:
        return None

    value = value.strip().replace(",", "")

    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None



prompt = """
첨부된 실제 식품 영양정보 라벨 사진에서 영양 정보를 추출하라.

반드시 이미지에 직접 읽을 수 있는 정보만 사용한다.

외부 지식으로 상품명이나 값을 추측하지 않는다.

규칙:
- 숫자 값은 이미지에 표시된 숫자만을 읽는다.
- 숫자 필드는 단위를 제외한 숫자 부분만 짧은 문자열로 기록한다.
  예: 
  350 kcal -> "350"
  9 g -> "9"
  0.4 g -> "0.4"

- 상품명이 이미지에서 보이지 않으면 product_name은 null로 기록한다.
- 존재하지 않거나 읽을 수 없는 항목은 unreadable_or_missing_fields에도 기록한다. 
- 같은 숫자나 문장을 반복하지 않는다.
- 각 필드의 값은 한 번만 작성한다.
- 설명 문장이나 Markdown을 추가하지 않는다.
- 최종 결과만 Structured Output으로 반환한다.
"""

def extract_nutrition():
    interaction = client.interactions.create(
        model='gemini-3.7-flash',
        input=[
            {
                'type': 'text',
                'text': prompt
            },
            {
                'type':'image',
                'uri': upload_file.uri,
                'mime_type': upload_file.mime_type
            }
        ],
        generation_config={
            'thinking_level': 'low'
        },
        response_format={
            'type': 'text',
            'mime_type': 'application/json',
            'schema': NutritionLabelRaw.model_json_schema()
        }
    )

    return interaction

interaction = extract_nutrition()

raw_json = interaction.output_text

print_title('response json')
print(f'json 문자 길이: {len(raw_json)}')
print(raw_json[:2000])

try:
    raw_result = NutritionLabelRaw.model_validate_json(raw_json)
except ValidationError as error:
    print_title('첫 번째 sturctured output 파싱 실패')
    print(error)
    print('\ngemini에게 다시 한 번 요청함')

    interaction = extract_nutrition()
    raw_json = interaction.output_text

    raw_result = NutritionLabelRaw.model_validate_json(raw_json)



result = NutritionLabelResult(
    product_name=raw_result.product_name,
    serving_basis=raw_result.serving_basis,
    energy_kj=to_int(raw_result.energy_kj),
    calories_kcal=to_int(raw_result.calories_kcal),                     
    protein_g=to_float(raw_result.protein_g),
    carbohydrate_g=to_float(raw_result.carbohydrate_g),
    sugars_g=to_float(raw_result.sugars_g),
    fat_g=to_float(raw_result.fat_g),
    saturates_g=to_float(raw_result.saturates_g),
    fibre_g=to_float(raw_result.fibre_g),
    sodium_text=raw_result.sodium_text,
    extraction_confidence=raw_result.extraction_confidence,
    unreadable_or_missing_fields=raw_result.unreadable_or_missing_fields
)

print_title('최종 결과')
print(f'상품명: {result.product_name}')
print(f'기준: {result.serving_basis}')
print(f'Energy: {result.energy_kj}')
print(f'Calories: {result.calories_kcal}')
print(f'Protein: {result.protein_g}')
print(f'Carbohydrate: {result.carbohydrate_g}')
print(f'Sugars: {result.sugars_g}')
print(f'Fat: {result.fat_g}')
print(f'Saturates: {result.saturates_g}')
print(f'Fibre: {result.fibre_g}')
print(f'Sodium: {result.sodium_text}')
