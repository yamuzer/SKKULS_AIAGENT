import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import csv


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

OUTPUT_CSV_PATH = BASE_DIR / 'data' / 'url_context_report.csv'

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.6-flash"

def print_title(title:str):
    print('\n' + '-' * 80)
    print(title)
    print('-' * 80)
    print()

TARGET_URL = 'https://docs.python.org/3.14/whatsnew/3.14.html'

prompt = f"""
다음 URL의 웹페이지를 URL Context Tool로 직접 읽고,
그 페이지에 적힌 내용만 근거로 한국어로 답하라.

URL:
{TARGET_URL}

다음 항목을 정리하라.

1. 페이지 제목
2. Python 3.14의 공식 릴리스 날짜
3. 페이지의 Summary - Release highlights에서 가장 큰 변화로 소개한 핵심 기능 3개
4. 표준 라이브러리에 추가된 Zstandard 관련 기능
5. multiple interpreters가 Python 3.14에서 어떻게 달라졌는지
6. free-threaded mode와 관련된 Python 3.14의 중요한 변화
7. 이 페이지에 근거해서 Python 3.13 사용자가 3.14로 넘어갈 때 
   특히 살펴볼 만한 항목 3개

주의:

- Google Search를 사용하지 않는다.
- 제공한 URL의 내용만 근거로 답한다.
- 페이지에서 확인할 수 없는 내용은 추측하지 않는다.
"""

interaction = client.interactions.create(
    model=MODEL_NAME,
    input=prompt,
    tools=[
        {
            "type": "url_context"
        }
    ]
)

print_title("1. gemini url context result")
#print(interaction.output_text)

steps = interaction.steps or []

url_call_steps = [
    step
    for step in steps
    if getattr(step, 'type', None) == 'url_context_call'
]

print_title('2. url context call')
print(f'url_context_call 개수: {len(url_call_steps)}')

for step in url_call_steps:
    arguments = getattr(step, 'arguments', None)
    urls = getattr(arguments, 'urls', None) or []

    for url in urls:
        print(f'gemini가 가져오도록 요청한 url: {url}')


url_result_steps = [
    step
    for step in steps
    if getattr(step, 'type', None) == 'url_context_result'
]

print_title('3. url context result')
print(f'url_context_result 개수 : {len(url_result_steps)}')

retrieval_rows = []

for step in url_result_steps:
    result_items = getattr(step, 'result', None) or []

    for item in result_items:
        status = getattr(item, 'status', None)
        url = getattr(item, 'url', None)
        title = getattr(item, 'title', None)
        snippet = getattr(item, 'snippet', None)

        print(f'\nURL: {url}')
        print(f'\nstatus: {status}')
        if title:
            print(f'\ntitle: {title}')
        if snippet:
            print(f'\nsnippet: {snippet}')

        retrieval_rows.append(
            {
                'record_type':'url_retrieval',
                'url':url or '',
                'status': status or '',
                'title': title or '',
                'cited_text': ''
            }
        )


citation_number = 1
# annotation 정보들을 풀어서 가져오기
for step in steps:
    if getattr(step, 'type', None) != 'model_output':
        continue

    content_blocks = getattr(step, 'content', None) or []

    for block in content_blocks:
        if getattr(block, 'type', None) != 'text':
            continue

        annotations = getattr(block, 'annotations', None) or []

        for annotation in annotations:
            if getattr(annotation, 'type', None) != 'url_citation':
                continue
            title = getattr(annotation, 'title', None)
            url = getattr(annotation, 'url', None)
            start_index = getattr(annotation, 'start_index', None)
            end_index = getattr(annotation, 'end_index', None)

            print(f'\ncitation #{citation_number}')
            print(f'title:{title}')
            print(f'url:{url}')
            print(f'start_index:{start_index}')
            print(f'end_index:{end_index}')

            retrieval_rows.append(
                {
                    'record_type':'citation',
                    'url':url or '',
                    'status':'',
                    'title':title or '',
                    'cited_text':f'응답 본문의 인용 범위 {start_index}:{end_index}'
                }
            )

            citation_number += 1


with OUTPUT_CSV_PATH.open(
    mode='w',
    newline='',
    encoding='utf-8-sig'
)as csv_file:
    fieldnames = [
        'record_type',
        'url',
        'status',
        'title',
        'cited_text'
    ]

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(retrieval_rows)

print(f'저장 경로: {OUTPUT_CSV_PATH}')