import os
from google import genai
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError('GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.')


client = genai.Client(api_key=api_key)

def ask_gemini_with_system(
    system_instruction:str,
    prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        system_instruction=system_instruction,
        input=prompt
    )
    return interaction.output_text

customer_message = """
지난주 월요일에 노트북을 주문했습니다.
원래 금요일까지 배송된다고 했는데 아직 상품을 받지 못했습니다.
택배 조회를 해보니 3일동안 물류센터에서 이동하지 않고 있습니다.
이 노트북은 다음 주 월요일 회사 발표에 사용해야 해서 반드시 필요합니다.
오늘 안에 배송 여부를 확실히 알 수 없다면 주문을 취소하고 전액 환불받고 싶습니다.
주문 번호는 ORD-2026-0813-1057 입니다.
"""

system_instruction = """
당신은 온라인 쇼핑몰의 고객 지원 AI상담원이다.
다음 규칙을 항상 따른다.

[역할]
고객 문의를 정확하게 파악하고 고객지원 담당자가 사용할 수 있는 신중한 답변을 생성한다.

[사실 사용 규칙]
1. 고객이 제공한 정보만 사실로 간주한다.
2. 확인되지 않는 배송 상태, 환불 완료 여부, 주문 처리 상태를 만들지 않는다.
3. 확인할 수 없는 내용은 확인이 필요하다고 명확하게 말한다.

[응답 규칙]
1. 고객의 핵심 문제를 먼저 파악한다.
2. 고객의 최종 요구사항을 확인한다.
3. 실제 확인이 필요한 업무를 구분한다.
4. 고객에게 확정되지 않은 내용을 확정된 것처럼 말하지 않는다.
5. 답변은 친절하고 간결하게 작성한다.

[금지 사항]
- 존재하지 않ㄴ는 배송 정보를 생성하지 않는다.
- 환불이 완료되었다고 임의로 말하지 않는다.
- 고객이 말하지 않는 주문 정보를 생성하지 않는다.
"""

user_prompt = f"""
다음 고객 문의를 분석하고 고객에게 적절한 답변을 작성해줘.
[고객 문의]
{customer_message}
"""

result_with_system = ask_gemini_with_system(
    system_instruction=system_instruction,
    prompt = user_prompt
)
print(result_with_system)