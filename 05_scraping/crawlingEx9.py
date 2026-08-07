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

    #print(soup.select('.product-card:not(.featured)'))

    #print(soup.select('.product-card:has(.stock-status.sold-out)'))

    #내부에 available 요소가 있고 feature가 아닌 상품
    #print(soup.select('.product-card:not(.featured):has(.stock-status.available)'))


    # important_texts = soup.select('#page-title, .page-description, .summary-section>h2')
    # print(important_texts)

    menu_links = soup.select('.category-menu > li > a')
    for link in menu_links:
        print(f'텍스트={link.get_text()}, href={link.get("href")}')


















if __name__ == '__main__':
    main()