import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
#  pip install langchain=1.2.17

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

MODEL_NAME=('gemini-3.7-flash')

gemini_client = genai.Client(api_key=api_key)

def print_title(title:str)-> None:
    print('\n'+'='*80)
    print(title)
    print('='*80)
    print()

question = 'RAG를 이해할 수 있도록 3문장으로 설명해주세요.'

direct_response = gemini_client.models.generate_content(
    model=MODEL_NAME,
    contents=question
)

print_title('1. direct use')
print(direct_response.text)

model = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    api_key = api_key
)

response = model.invoke(question)

print_title('langchain use')
print(response.text)
print()
print(type(response))
print()
print(response.response_metadata)
print()
print(response.usage_metadata)

