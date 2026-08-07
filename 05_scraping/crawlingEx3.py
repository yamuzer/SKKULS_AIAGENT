from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / 'data' / 'product_list.html'
html_text = HTML_PATH.read_text(encoding='utf-8')
soup = BeautifulSoup(html_text, 'html.parser')

# product_names = soup.find_all('h2')
# print(product_names)
# print(len(product_names))
#
# for name in product_names:
#     print(name.get_text(strip=True))

div_tag = soup.find('div')
#print(div_tag)
price_tag = div_tag.find('span', class_='price')
print(price_tag.get_text())
