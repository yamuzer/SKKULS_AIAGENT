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

    cards = soup.select('.product-card')

    for card in cards:
        product_id = card.get('data-product-id')
        stock_count = card.get('data-stock-count')

        link_tag = card.select_one('a.product-link')
        href = link_tag.get('href')
        title = link_tag.get('title')

        print(
            f'상품번호: {product_id}, '
            f'상품명: {title}, '
            f'재고: {stock_count}, '
            f'링크: {href}'
        )

if __name__ == '__main__':
    main()