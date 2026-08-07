from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / 'data' / 'product_list.html'
html_text = HTML_PATH.read_text(encoding='utf-8')
soup = BeautifulSoup(html_text, 'html.parser')
heading = soup.find('h1')
print(heading)
print(heading.get_text())
print(heading.name)
print(heading.get('id'))
print(soup.find('p', {'class':'brand'}).get_text())
