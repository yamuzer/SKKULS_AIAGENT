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



prompt = """
python의 데코레이터에 대해 자세히 설명해줘
데코레이터의 장점을 3가지도 자세히 설명해줘

각 장점은 3줄 문장으로 구성해줘.
"""

def print_title(title: str) -> None:
    print('='*100)
    print(f'\n{title}')
    print('='*100)

result = ask_gemini_full(prompt=prompt)
print_title('interaction id')
print(result.id)

print_title('model')
print(result.model)


print_title('생성 시간 / 수정 시간')
print('created:', result.created)
print('updated:', result.updated)


'''
print_title('step 상세확인')

from pprint import pprint

for index, step in enumerate(result.steps, start=1):
    print(f'[step {index}]')
    pprint(step.model_dump(exclude_none=True))
'''


print_title('Token usage')

if result.usage:
     print(f'input tokens: {result.usage.total_input_tokens}')
     print(f'output tokens: {result.usage.total_output_tokens}')
     print(f'thought tokens: {result.usage.total_thought_tokens}')
     print(f'total tokens: {result.usage.total_tokens}')