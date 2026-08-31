import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv
import wave
from pydantic import BaseModel, Field, ValidationError
from typing import Literal


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / '.env'

AUDIO_PATH = BASE_DIR / "data" / "pyannote_two_speaker_sample.wav"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError('GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.')

if not AUDIO_PATH.exists():
    raise FileNotFoundError(f'오디오 파일을 찾을 수가 없습니다 {AUDIO_PATH}')


client = genai.Client(api_key=api_key)


def print_title(title: str) -> None:
    print('='*100)
    print(f'{title}')
    print('='*100)
    print()


with wave.open(str(AUDIO_PATH)) as wav_file:
    channels = wav_file.getnchannels()
    sample_rate = wav_file.getframerate()
    frame_count = wav_file.getnframes()
    sample_width = wav_file.getsampwidth()

    duration_seconds = frame_count / sample_rate


print_title('local wav metadata')
print(f'파일명: {AUDIO_PATH.name}')
print(f'채널 수: {channels}channels')
print(f'sample rate: {sample_rate}Hz')
print(f'sample width: {sample_width}bytes')
print(f'재생 길이: {round(duration_seconds, 3)}')

 # 발화 구간(segment)의 데이터 구조 정의
class AudioSegment(BaseModel):
    speaker:str = Field(
        description='화자 라벨. 실제 신원을 추측하지말고 Speaker1, Speaker2처럼 작성'
    )

    speaker_name_if_spoken: str | None = Field(
        description='화자가 오디오 안에서 자신의 이름을 직접 말한 경우 그 이름. 직접 확인되지 않으면 null'
    )

    start_time: str = Field(
        description='발화 시작 시각. MM:SS.xx 형태의 근사값'
    )

    end_time: str = Field(
        description='발화 종료 시각. MM:SS.xx 형태의 근사값'
    )

    translation_en: str = Field(
        description='해당 구간에서 들리는 영어 발화를 가능한 정확하게 전사'
    )

    translation_ko: str = Field(
        description='해당 발화의 자연스러운 한국어 번역'
    )

    emotion: Literal[
        'happy',
        'sad',
        'angry',
        'neutral',
        'uncertain'
    ] = Field(
        description='해당 구간에서 들리는 주된 감정. 불확실하면 uncertain'
    )

    confidence: Literal[
        '높음',
        '보통',
        '낮음'
    ] = Field(
        description='해당 구간의 전사 및 화자 구분에 대한 전체적인 신뢰도'
    )

# 전체 분석 결과 구조
class AudioStructuredResult(BaseModel):
    detected_language: str = Field(
        description='오디오에서 확인되는 주된 언어'
    )

    speaker_count: str = Field(
        description='오디오에서 구분되는 화자 수'
    )

    summary_ko: str = Field(
        description='전체 대화 내용을 한국어 2~4문장으로 요약'
    )

    segments: list[AudioSegment] = Field(
        description='시간 순서대로 정리한 발화 구간 목록'
    )

    key_point_ko: list[str] = Field(
        description='대화에서 확인되는 핵심 내용 목록'
    )

    non_speech_sounds: list[str] = Field(
        description='비프음, 잡음 등 명확하게 들리는 비언어적 소리 목록'
    )

    uncertain_items : list[str] = Field(
        description='정확하게 확인하기 어려운 발화나 화자 구분 관련 사항'
    )


prompt = """
첨부된 전화 대화 오디오를 처음부터 끝까지 분석하라.

목표는 단순 요약이 아니라
"구간별 전사 + 화자 구분 + 번역 + 핵심 정보 추출"이다.

다음 원칙을 지킨다.
- 오디오에 직접 들리는 내용만 사용한다.
- 실제 화자의 신원을 외부 지식으로 추측하지 않는다.
- 화자는 Speaker 1, Spearker 2처럼 일관된 라벨을 사용한다.
- 오디오 안에서 화자가 자신의 이름을 직접 말하면 speaker_name_if_spoken에 기록할 수 있다.
- 발화 순서를 유지한다.
- start_time과 end_time은 MM:SS.xx 형태의 근사 타임스탬프로 기록한다.
- 영어 발화는 translation_en에 기록한다.
- 각 영어 발화를 translation_ko에 자연스럽게 번역한다.
- 비프음이나 전화 잡음 같은 비언어적 소리가 명확하면 non_speech_sounds에 기록한다.
- 감정을 과도하게 추측하지 않는다.
- 잘 들리지 않는 내용은 임의로 만들어내지 말고 confidence를 낮추거나 uncertain_items에 기록한다.
- 같은 문장이나 숫자를 반복 생성하지 않는다.
- Markdown 설명을 추가하지 말고 Structured Output만 반환한다.
"""

uploaded_audio = client.files.upload(file=str(AUDIO_PATH))


def request_audio_analysis():
    return client.interactions.create(
        model='gemini-3.7-flash',
        input=[
            {
                'type': 'text',
                'text': prompt
            },
            {
                'type': 'audio',
                'uri': uploaded_audio.uri,
                'mime_type': uploaded_audio.mime_type
            }
        ],
        generation_config={
            'thinking_level': 'low'
        },
        response_format={
            'type': 'text',
            'mime_type': 'application/json',
            'schema': AudioStructuredResult.model_json_schema()
        }
    )


interaction = request_audio_analysis()
raw_json = interaction.output_text
print_title('raw structured output')
print(f'json 문자 길이:{len(raw_json)}', end='\n\n')
print(raw_json)

try:
    result = AudioStructuredResult.model_validate_json(raw_json)
except ValidationError as first_error:
    print('\n첫 번째 JSON parsing 실패')

    interaction = request_audio_analysis()
    raw_json = interaction.output_text

    result = AudioStructuredResult.model_validate_json(raw_json)