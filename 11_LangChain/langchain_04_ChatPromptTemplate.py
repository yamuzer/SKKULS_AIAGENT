import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

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

print_title('chatPromptTemplate')
print(type(prompt))
print()
print(prompt)
print()
print(prompt.input_variables)
print()

first_input = {
    'level': '초보자',
    'topic': 'RAG',
    'question':(
        'RAG가 왜 필요한지 3문장으로 설명해주세요.'
    )
}

first_prompt_vlaue = prompt.invoke(first_input)
print_title('ChatPromptTemplate invoke')
# print(first_prompt_vlaue.messages)


for index, message in enumerate(first_prompt_vlaue.messages, start=1):
    print(f'\n{[index]}')
    print(f'message type:{type(message).__name__}')

    if hasattr(message, 'text'):
        print(message.text)
    else:
        print(message.content)


first_response = model.invoke(first_prompt_vlaue)
print_title('first response')
print(first_response.text)

second_input = {
    'level': '중급자',
    'topic': 'vector DB',
    'question':(
        '일반 데이터베이스와 벡터 데이터베이스와의 차이를'
        '핵심 3가지로 설명해주세요.'
    )
}

second_prompt_value = prompt.invoke(second_input)
second_response = model.invoke(second_prompt_value)
print_title('second response')
print(second_response.text)

level_str1 = '초보자'
level_str2 = '고급자'

topic_str = 'Embedding'

compare_question = 'Embedding이 검색에서 어떤 역할을 하는지 설명해주세요.'

beginner_value = prompt.invoke(
    {
        'level' : level_str1,
        'topic': topic_str,
        'question': compare_question
    }
)

expert_value = prompt.invoke(
    {
        'level' : level_str2,
        'topic': topic_str,
        'question': compare_question
    }
)

beginner_response = model.invoke(beginner_value)
expert_response = model.invoke(expert_value)
print_title('variable use')
print('beginner')
print(beginner_response.text)
print()

print('expert')
print(expert_response.text)
print()