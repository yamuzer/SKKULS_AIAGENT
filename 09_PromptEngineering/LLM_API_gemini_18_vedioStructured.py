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


class VideoSegment(BaseModel):
    start_time: str = Field(
        description='구간 시작 시각. MM:SS 형식'
    )

    end_time: str = Field(
        description='구간 종료 시각. MM:SS 형식'
    )

    event: str = Field(
        description='해당 구간에서 직접 확인되는 핵심 사건 또는 상태 변화'
    )

    main_objects: list[str] = Field(
        description='구간에서 명확하게 확인되는 주요 객체 목록'
    )

    visual_change: str = Field(
        description='구간 시작과 끝 사이의 주요 시각적 변화'
    )

    motion_type: Literal[
        'rotation',
        'translation',
        'appearance',
        'disappearance',
        'scene_change',
        'litte_or_no_change',
        'uncertain'
    ] = Field(
        description='구간의 대표적인 움직임 또는 변화 유형'
    )

    scene_change: bool = Field(
        description='다른 장면으로 전환되는 명확한 Scene Cut이 있는지 여부'
    )

    audio_observation: str = Field(
        description='구간에서 명확하게 들리는 Speech, Music 또는 Sound. 의미 있는 Audio가 없으면 null'
    )

    confidence: Literal[
        '높음',
        '보통',
        '낮음'
    ] = Field(
        description='해당 구간 분석의 신뢰도'
    )

class VideoTimelineResult(BaseModel):
    video_summary: str = Field(
        description='Video 전체 내용을 한국어 2~4문장으로 요약'
    )

    dominant_object: str = Field(
        description='Video 전체에서 가장 중심적인 객체 또는 장면'
    )

    overall_motion: str = Field(
        description='Video 전체에서 관찰되는 대표적인 시간적 변화'
    )

    continuous_scene: bool = Field(
        description='Video가 대체로 하나의 연속 장면으로 유지되는지 여부'
    )

    segments: list[VideoSegment] = Field(
        description=(
            '00:00~00:05, 00:05~00:10, 00:10~00:15, '
            '00:15~00:20, 00:20~00:25, 00:25~00:30의 시간 순서 Timeline 구간'
        )
    )

    key_changes: list[str] = Field(
        description='Video 전체에서 확인되는 중요한 변화 목록'
    )

    uncertain_items: list[str] = Field(
        description='Video만으로 확정하기 어려운 사항 목록 '
    )


prompt = """
첨부된 Video를 처음부터 끝까지 분석하라.

목표는 Video의 시간 흐름을 구조화된 Timeline 데이터로 변환하는 것이다.

Video에서 직접 확인할 수 있는 시각적 정보와 명확하게 들리는 Audio 정보만을 사용한다.

다음 6개 시간 구간을 모두 분석한다.

- 00:00 ~ 00:05
- 00:05 ~ 00:10
- 00:10 ~ 00:15
- 00:15 ~ 00:20
- 00:20 ~ 00:25
- 00:25 ~ 00:30

각 구간에서 다음 정보를 판단한다.
- 핵심 사건 또는 상태 변화
- 주요 객체
- 구간 시작과 끝 사이의 시각적 변화
- 대표적인 움직임 유형
- 명확한 Scene Cut 여부
- 의미 있는 Audio가 있는지 여부
- 분석 신뢰도

중요한 규칙:
- 실제 Video에서 보이는 내용만 사용한다.
- 정확한 제작자, 제작 장소, 제작 목적은 추측하지 않는다.
- 하나의 시점에서 보이지 않는 객체가 실제로 사라졌다고 단정하지 않는다.
- Scene Cut과 객체의 지속적인 움직임을 구분한다.
- 작은 세부사항이 확실하지 않으면 uncertain_items에 기록한다.
- Timestamp는 MM:SS 형식을 사용한다.
- 같은 문장이나 같은 값을 반복 생성하지 않는다.
- Markdown 설명을 추가하지 않는다.
- 최종 Structured Output만 반환한다.
"""



interaction1 = client.interactions.create(
    model='gemini-3.7-flash',
    input=[
        {
            'type': 'video',
            'uri': uploaded_video.uri,
            'mime_type': uploaded_video.mime_type
        },
        {
            'type': 'text',
            'text': prompt
        }
    ],
    generation_config= {
        'thinking_level': 'low'
    },
    response_format={
        'type':'text',
        'mime_type': 'application/json',
        'schema': VideoTimelineResult.model_json_schema()
    }
)

print_title('Video Sturctured_output')
print(interaction1.output_text)

try:
    result = VideoTimelineResult.model_validate_json(interaction1.output_text)
except ValidationError as first_error:
    print('\n 첫 번째 json parsing error')
