# id 없으면 히스토리 유지 안됨.
# 티어에 따라 하루에서 수일 정도. 서비스 정책에 따라 달라짐.
# 일회성 대화. 세션용
# 서비스하려면 히스토리 DB구축해야함

import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / '.env'

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError('GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.')


client = genai.Client(api_key=api_key)


def print_title(title: str) -> None:
    print('='*100)
    print(f'\n{title}')
    print('='*100)

def ask_gemini(prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt
    )

    return interaction.output_text


def ask_gemini_with_system(
    system_instruction: str,
    prompt: str
) -> str:
    
    interaction = client.interactions.create(
        model='gemini-3.7-flash',
        system_instruction=system_instruction,
        input=prompt
    )

    return interaction.output_text

def ask_gemini_full(prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.7-flash',
        input=prompt
    )

    return interaction

def ask_gemini_send_id(
    previous_id,
    prompt: str
) -> str:
    interaction = client.interactions.create(
        model='gemini-3.7-flash',
        input=prompt,
        previous_interaction_id=previous_id
    )

    return interaction



first_prompt = """
다음 정보를 기억해주세요.

제이름은 홍길동입니다.
저는 ai를 공부하고 있습니다.
관심분야는 ai를 이용한 에이전트입니다.
"""

interaction1 = ask_gemini_full(prompt=first_prompt)
print_title('첫 번째 대화')
print(interaction1.output_text)

second_prompt = """
제가 공부하고 있다고 말한 분야는 무엇인가?
"""

interaction2 = ask_gemini_send_id(
    previous_id=interaction1.id,
    prompt=second_prompt)
print_title('두 번째 대화')
print(interaction2.output_text)
