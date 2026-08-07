from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / 'data' / 'product_list.html'
html_text = HTML_PATH.read_text(encoding='utf-8')
soup = BeautifulSoup(html_text, 'html.parser')

article = soup.find('article', {'data-product-id':'1008'})
print(article.select_one('.rating').get_text())