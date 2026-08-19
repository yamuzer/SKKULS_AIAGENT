import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv
import wave
from pydantic import BaseModel, Field, ValidationError
from typing import Literal
import time


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / '.env'

VIDEO_PATH = BASE_DIR / "data" / "video_world_gradio.mp4"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError('GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.')

if not VIDEO_PATH.exists():
    raise FileNotFoundError(f'Video 파일을 찾을 수가 없습니다 {VIDEO_PATH}')


client = genai.Client(api_key=api_key)


def print_title(title: str) -> None:
    print('='*100)
    print(f'{title}')
    print('='*100)
    print()


uploaded_video = client.files.upload(file=str(VIDEO_PATH))
print(f'mime_type: {uploaded_video.mime_type}')

while True:
    state_name = getattr(
        uploaded_video.state,
        'name',
        None
    )

    if state_name == 'ACTIVE':
        break

    if state_name == 'FAILED':
        raise RuntimeError('gemini에서 Video preprocessing에 실패했습니다.')

    print(f'Video preprocessing 중... 현재 상태: {state_name}')

    time.sleep(5)

    uploaded_video = client.files.get(name=uploaded_video.name)

print(f'Video preprocessing 완료: {getattr(uploaded_video.state, 'name', None)}')


prompt = """
첨부된 Video를 처음부터 끝까지 관찰하고 한국어로 분석하라.

Video에서 직접 확인할 수 있는 시각적 정보와 명확하게 들리는 오디오 정보만을 사용한다.

확인할 수 없는 장소, 제작 목적, 제작자 등의 정보는 임의로 추측하지 않는다.

다음 순서로 답하라.
1. Video 전체를 2~3문장으로 설명
2. 화면에서 가장 중심적으로 보이는 객체 또는 장면
3. Video가 진행되면서 가장 눈에 띄는 움직임 또는 변화
4. 배경과 색상, 밝기에서 확인되는 특징
5. 화면에서 명확하게 읽을 수 있는 Text가 있는지
6. 의미 있는 Speech, Music 또는 다른 Audio가 들리는지
7. 00:00, 00:10, 00:20, 00:30 부근에서 화면이 어떻게 달라지는지 비교
8. Video만으로 확정할 수 없는 상황

마지막에는 핵심 내용을 2문장으로 요약한다.
"""

interaction1 = client.interactions.create(
    model='gemini-3.7-flash',
    input=[
        {
            'type': 'text',
            'text': prompt
        },
        {
            'type': 'video',
            'uri': uploaded_video.uri,
            'mime_type': uploaded_video.mime_type
        }

    ]
)

print_title('Video 기본 분석')
print(interaction1.output_text)