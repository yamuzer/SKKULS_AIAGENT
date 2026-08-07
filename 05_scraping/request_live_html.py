import requests
from bs4 import BeautifulSoup


URL = "https://finance.naver.com/sise/sise_market_sum.naver"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.7,en;q=0.5",
    "Referer": "https://finance.naver.com/",
}

TIMEOUT = 20


def request_market_page(
    market_code: str = "0",
    page: int = 1,
) -> requests.Response:
    """
    네이버 금융 시가총액 페이지를 실제 요청합니다.

    market_code:
        "0" = 코스피
        "1" = 코스닥
    """

    params = {
        "sosok": market_code,
        "page": page,
    }

    response = requests.get(
        URL,
        params=params,
        headers=HEADERS,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    # 한글 인코딩 오판을 방지합니다.
    response.encoding = (
        response.apparent_encoding
        or "euc-kr"
    )

    return response


MARKET_CODE = "0"
PAGE = 1


response = request_market_page(
    market_code=MARKET_CODE,
    page=PAGE,
)

soup = BeautifulSoup(
    response.text,
    "html.parser",
)


print("=" * 72)
print("1. requests로 네이버 금융 실제 접속")
print("=" * 72)

print("최종 요청 URL:", response.url)
print("상태 코드:", response.status_code)
print("응답 인코딩:", response.encoding)
print("Content-Type:", response.headers.get("Content-Type"))
print("HTML 문자 수:", len(response.text))

print()
print("[문서 title]")

if soup.title:
    print(
        soup.title.get_text(
            " ",
            strip=True,
        )
    )
else:
    print("title 없음")

print()
print("[HTML 앞부분]")
print(response.text[:600])
