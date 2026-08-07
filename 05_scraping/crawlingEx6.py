from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / 'data' / 'product_list.html'


def load_soup() -> BeautifulSoup:
    html_text = HTML_PATH.read_text(encoding='utf-8')
    return BeautifulSoup(html_text, 'html.parser')

def main() -> None:
    soup = load_soup()

    #print(soup.select('.product-info > .product-name'))

    direct_cards = soup.select('#product-list > article.product-card')
    print(len(direct_cards))

    for tag in direct_cards:
        print('-', tag.get_text(strip=True, separator=' '), end='\n\n')


if __name__ == '__main__':
    main()