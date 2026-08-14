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

def ask_gemini(prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt
    )
    return interaction.output_text

customer_message = """
상품이 아직 도착하지 않았는데 더 이상 기다리고 싶지 않아 환불받고 싶습니다.
"""

prompt_few_shot = f"""
다음 고객 문의를 아래 카테고리 중 하나로 분류해줘.

카테고리:
- 배송 
- 환불
- 제품불량

[예제 1]
고객 문의: '배송 예정일이 지났는데 아직 상품이 도착하지 않았습니다.'
분류 : 배송

[예제 2]
고객 문의: '제품을 받았는데 전원이 전혀 켜지지 않습니다.'
분류 : 제품불량

[예제 3]
고객 문의: '상품이 늦게 도착해서 더 이상 필요하지 않습니다. 환불 받고 싶습니다.'
분류 : 환불

[예제 4]
고객 문의: '제품에 흠집이 있고 정상적으로 동작하지 않습니다.'
분류 : 제품 불량


[분류할 문의]
고객 문의 : "{customer_message}"
분류 : 
"""

result_few_shot = ask_gemini(
    prompt_few_shot
)
print(result_few_shot)