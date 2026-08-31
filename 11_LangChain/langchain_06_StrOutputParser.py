import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

MODEL_NAME=('gemini-3.7-flash')

model = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    api_key=api_key
)

def print_title(title:str)-> None:
    print('\n'+'='*80)
    print(title)
    print('='*80)
    print()

prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            (
                '당신은 AI와 Python을 자세히 아려주는 도우미입니다.'
                '학습자 수준은 {level}입니다.'
                '{topic}주제를 학습자 수준에 맞게 쉽고 정확하게 설명하세요.'
            ),
        ),
        (
            'human',
            '{question}'
        )
    ]
)

parser = StrOutputParser()
print(type(parser))



input_data = {
    'level' : '초보자',
    'topic' : 'Embedding',
    'question' : (
        'Embedding이 무엇인지 5문장으로 설명해 주세요.'
    )
}


chain = (prompt | model)
print_title('chain use')
print(type(chain))

chain_response = chain.invoke(input_data)
message_result = parser.invoke(chain_response)
print_title('StrOutputParser 실행')
print(message_result)

print_title('prompt | model | parser')

chain2 = (prompt | model | parser) # 결과물에서 text만 추출
print(chain2.invoke(input_data))
