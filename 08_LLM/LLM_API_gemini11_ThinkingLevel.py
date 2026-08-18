import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv
import time


BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / '.env'

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


def ask_gemini_thinking_mode(
    thinking_level: str,
    prompt: str
) -> str:


    print_title(thinking_level.upper())

    start_time = time.perf_counter()
    
    interaction = client.interactions.create(
        model='gemini-3.7-flash',
        input=prompt,
        generation_config={
            'thinking_level': thinking_level
        }
    )

    end_time = time.perf_counter()

    elapsed_time = end_time - start_time

    print(f'thinking level : {thinking_level.upper()}')
    print(f'응답 시간: {elapsed_time:.2f}')
    print('[gemini] 응답:')
    print(interaction.output_text, end='\n\n')

    

    if interaction.usage:
     print(f'input tokens: {interaction.usage.total_input_tokens}')
     print(f'output tokens: {interaction.usage.total_output_tokens}')
     print(f'thought tokens: {interaction.usage.total_thought_tokens}')
     print(f'total tokens: {interaction.usage.total_tokens}')

    print()
    return interaction

prompt = """
한 회사가 세 개의 프로젝트 중 하나를 선택하려고 한다.

프로젝트 A
- 개발 비용: 5억원
- 예상 연간 수익: 8억원
- 실패 확률: 20%

프로젝트 B
- 개발 비용: 3억원
- 예상 연간 수익: 5억원
- 실패 확률: 10%

프로젝트 C
- 개발 비용: 8억원
- 예상 연간 수익: 13억원
- 실패 확률: 35%

단순 예상 이익뿐 아니라 실패 위험도까지 함께 고려하여 가장 적절한 프로젝트를 하나 추천하고
근거를 설명한다.
"""

lower_result = ask_gemini_thinking_mode(
    thinking_level='low',
    prompt=prompt
)


medium_result = ask_gemini_thinking_mode(
    thinking_level='medium',
    prompt=prompt
)


high_result = ask_gemini_thinking_mode(
    thinking_level='high',
    prompt=prompt
)