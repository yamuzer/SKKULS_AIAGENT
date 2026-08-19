import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv
import wave


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / '.env'

AUDIO_PATH = BASE_DIR / "data" / "audio_applause_real.wav"

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



uploaded_audio = client.files.upload(file=str(AUDIO_PATH))

print(f'mime_type: {uploaded_audio.mime_type}')

audio_token_result = client.models.count_tokens(
    model='gemini-3.7-flash',
    contents=[uploaded_audio]
)

print_title('Audio token count')
print(f'audio token: {audio_token_result.total_tokens}')

prompt1 = """
첨부된 오디오를 처음부터 끝까지 듣고 분석하라.

오디오에서 직접 들을 수 있는 정보만 사용한다.
정확한 장소, 행사명, 인물의 신원 등은 근거 없이 추측하지 않는다.

다음 순서로 한국어로 답하라.
1. 가장 중심적으로 들리는 소리는 무엇인가?
2. 이 오디오는 다음 중 어디에 가장 가까운가?
    - speech
    - music
    - human-generated sound
    - environmental sound

3. 사람이 말하는 명확한 문장이나 단어가 들리는가? 
   들린다면 내용을 적고, 명확하지 않으면 '명확한 발화 확인 어려움'이라고 작성한다.
4. 중심 소리 외에 함께 들리는 다른 소리가 있는가?
5. 소리의 강도와 분위기가 처음부터 끝까지 어떻게 변하는가?
6. 이 소리가 발생할 수 있는 상황을 일반적인 수준에서 설명하라. 
   특정 행사나 장소라고 단정하지 않는다.
7. 확실하게 판단하기 어려운 사항이 있다면 정리한다.

마지막에는 핵심 내용을 2문장으로 요약한다.
"""

interactions1 = client.interactions.create(
    model='gemini-3.7-flash',
    input=[
        {
            'type':'text',
            'text': prompt1
        },
        {
            'type': 'audio',
            'uri': uploaded_audio.uri,
            'mime_type': uploaded_audio.mime_type
        }
    ]
)

print_title('기본 audio 분석')
print(interactions1.output_text)