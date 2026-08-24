import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv
import time


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / '.env'
FILE_PATH = BASE_DIR / 'data' / 'seoul_station_2012.jpg'


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

def ask_gemini(prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt
    )

    return interaction.output_text

upload_file = client.files.upload(file=str(FILE_PATH))

file_info = client.files.get(name=upload_file.name)
# print(file_info)

prompt1 = """
첨부된 사진을 관찰하고 사진에서 직접 확인할 수 있는 내용만 분석하라.
다음 순서로 답하라.
1. 장면 전체를 2~3문장으로 설명
2. 눈에 띄는 주요 객체를 종류별로 정리
3. 사람과 차량의 위치 및 움직임을 간단하게 설명
4. 사진 속 글자나 표지판 중 비교적 명확하게 읽을 수 있는 것을 정리
5. 이 장소가 어떤 종류의 장소로 보이는지 설명
6. 확실하지 않은 내용은 추측하지 말고 "확인 어려움"이라고 표시
사람의 이름이나 신원을 추측하지 않는다.
"""

interaction1 = client.interactions.create(
    model='gemini-3.7-flash',
    input=[
        {
            'type':'text',
            'text': prompt1

        },
        {
            'type':'image',
            'uri': upload_file.uri,
            'mime_type' : upload_file.mime_type
        }
    ]
)

print(interaction1.output_text)