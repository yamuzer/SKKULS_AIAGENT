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

def ask_gemini(
    prompt: str) -> str:
    interaction = client.interactions.create(
        model='gemini-3.6-flash',
        input=prompt
    )
    return interaction.output_text

review = """
배송은 예상보다 하루 늦었습니다.
제품 포장은 조금 찌그러져 있었지만 제품 자체에는 문제가 없습니다.
무선 마우스의 연결 속도와 사용감은 상당히 만족스럽습니다.
다만 가격이 비슷한 제품보다 조금 비싼 것 같습니다.
전체적으로 만족하지만 다음에 다시 구매할지는 잘 모르겠습니다.
"""

prompt_rtf = f"""
[Role]
너는 온라인 쇼핑몰의 고객 리뷰를 분석하는 VOC 데이터 분석가다.

[Task]
다음 고객 리뷰를 분석하라.
리뷰에서 다음 내용을 파악한다.
- 전체적인 고객 감정
- 만족한 부분
- 재구매 가능성
- 개선이 필요한 부분

[CUstomer Review]
{review}

[Format]
다음 형식으로 작성하라.

전체 감정:
긍정 / 중립 / 부정 중 하나

만족 요소 : 
- 
-

불만 요소:
-
-

재구매 가능성:
높음 / 보통 / 낮음 중 하나

개선 필요 사항 :
1.
2.

한줄 요약 :
"""

rtf_result = ask_gemini(prompt=prompt_rtf)
print(rtf_result)