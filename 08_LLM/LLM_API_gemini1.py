import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError('GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.')

client = genai.Client(
    api_key = api_key
)
print(client)

interaction = client.interactions.create(
    model='gemini-3.6-flash',
    input = (
        '파이썬의 generator를 프로그래밍 초보자에게 설명해줘'
    )
)

print(interaction.output_text)


