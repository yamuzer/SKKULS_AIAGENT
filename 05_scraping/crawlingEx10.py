from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / 'data' / 'product_list.html'


def load_soup() -> BeautifulSoup:
    html_text = HTML_PATH.read_text(encoding='utf-8')
    return BeautifulSoup(html_text, 'html.parser')


def print_name(tags) -> None:
    for tag in tags:
        print('-', tag.get_text(strip=True))


def main() -> None:
    soup = load_soup()

    headers = soup.select('.summary-table thead th')
    header_names = [tag.get_text() for tag in headers]
    print(header_names)
    print()

    rows = soup.select('.summary-table tbody > tr')

    for row in rows:
        cells = row.select(':scope > td')
        values = [cell.get_text(strip=True) for cell in cells]
        print(values)

















if __name__ == '__main__':
    main()