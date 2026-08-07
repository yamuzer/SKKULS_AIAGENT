from urllib.parse import urlparse, parse_qs, urljoin

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import query_expression

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


def extract_stock_code(stock_url: str) -> str:
    parsed_url = urlparse(stock_url)

    query_values = parse_qs(parsed_url.query)
    return query_values.get('code', [''])[0]


response = request_market_page(
    market_code=MARKET_CODE,
    page=PAGE
)

soup = BeautifulSoup(response.text, 'html.parser')

market_table = find_market_cap_table(soup)

stock_row = None

for row in market_table.select('tr'):
    cells = row.select(':scope > td')

    name_link = row.select_one(
        'a[href*="/item/main.naver?code="]'
    )

    if name_link is not None and len(cells) >= 12:
        stock_row = row
        break


#print(stock_row)

cells = stock_row.select(':scope > td')
#print(cells)
name_link = stock_row.select_one(
    'a[href*="/item/main.naver?code="]'
)
#print(name_link)

relative_url = name_link.get('href')


BASE_URL = "https://finance.naver.com"

stock_data = {
    'rank': cells[0].get_text(strip=True),
    'stock_code': extract_stock_code(relative_url),
    'stock_name': name_link.get_text(strip=True),
    'current_price': cells[2].get_text(strip=True),
    'change_text': cells[3].get_text(strip=True),
    'change_rate': cells[4].get_text(strip=True),
    'face_value': cells[5].get_text(strip=True),
    'market_cap': cells[6].get_text(strip=True),
    'listed_shares': cells[7].get_text(strip=True),
    'foreign_ratio': cells[8].get_text(strip=True),
    'volume': cells[9].get_text(strip=True),
    'per': cells[10].get_text(strip=True),
    'roe': cells[11].get_text(strip=True),
    'stock_url': urljoin(BASE_URL, relative_url),
    'source_url': response.url
}

for key, value in stock_data.items():
    print(f'{key:16}: {value}')
























