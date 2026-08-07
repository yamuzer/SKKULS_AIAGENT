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

    # print(soup.select('#product-list > article:first-of-type'))
    # print()
    #
    # print(soup.select('#product-list > article:last-of-type'))
    # print()

    # print(soup.select('#product-list > article:nth-of-type(odd)'))
    # print()

    print(soup.select('#product-list > article:nth-of-type(3n+1)'))
    print()
if __name__ == '__main__':
    main()