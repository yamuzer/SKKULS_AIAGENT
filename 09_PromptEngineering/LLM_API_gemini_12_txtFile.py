import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv
import time


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / '.env'
FILE_PATH = BASE_DIR / 'data' / 'company_policy.txt'


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
첨부된 교육센터 운영 정책 파일을 읽어라.
다음 내용을 중심으로 정리하라.

1. 교육 기간
2. 출석 기준
3. 평가 비율
4. 수료 기준
5. 프로젝트 운영 방식
6. 재평가 정책
파일에 없는 내용은 추측하지 않는다.
"""

interaction1 = client.interactions.create(
    model='gemini-3.7-flash',
    input=[
        {
            'type':'text',
            'text': prompt1

        },
        {
            'type':'document',
            'uri': upload_file.uri,
            'mime_type' : upload_file.mime_type
        }
    ]
)

print(interaction1.output_text)