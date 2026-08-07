from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / 'data' / 'product_list.html'
html_text = HTML_PATH.read_text(encoding='utf-8')
soup = BeautifulSoup(html_text, 'html.parser')

# page_title = soup.select_one('#page-title')
# print(page_title)
#
# page_description = soup.select_one('.page-description')
# print(page_description)

# product_card = soup.select_one('.product-card.featured')
# print(product_card)

# tags = soup.select('.page-description')
# print(tags[0])

for element in soup.select('.product-card'):
    print(element)
    print(element.get_text(), end='\n\n\n')