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

def find_market_cap_table(soup: BeautifulSoup):
    '''
    종목명, 현재가, 시가총액 열을 가지 표를 찾음
    '''

    required_headers = {
        '종목명',
        '현재가',
        '시가총액'
    }
    #print(soup.select('table'))
    for table in soup.select('table'):
        header_values = {
            th.get_text(strip=True) for th in table.select('th')
        }
        #print(header_values)

        if required_headers.issubset(header_values):
            return table

    return None



response = request_market_page(
    market_code=MARKET_CODE,
    page=PAGE
)

soup = BeautifulSoup(response.text, 'html.parser')

market_table = find_market_cap_table(soup)
print(market_table.get('class'))
print()

headers = [th.get_text(strip=True) for th in market_table.select('th')]
for index, header in enumerate(headers):
    print(index, header)





















