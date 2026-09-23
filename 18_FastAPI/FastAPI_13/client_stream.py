import httpx

URL = 'http://127.0.0.1:8000/llm/stream'


def main() -> None:

    payload = {
        'message':'FastAPI와 LLM Streaming의 관계를 자세히 설명해줘.',
        'system_prompt': '당신은 친절한 AI 헬퍼입니다.',
        'temperature': 0.2
    }

    print('\n--- Gemini Streaming Start ---\n')

    with httpx.stream(
        "POST",\
        URL,
        json=payload,
        timeout=None
    ) as response:
        response.raise_for_status()

        for text in response.iter_text():
            print(text, end='', flush=True)

    print('\n\n--- Gemini Streaming End ---')


if __name__ == "__main__":
    main()