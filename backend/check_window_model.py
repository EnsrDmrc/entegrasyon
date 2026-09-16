import json
from bs4 import BeautifulSoup
import sys
sys.path.append('./backend')

html_content = open('backend/n11_test.html', 'r', encoding='utf-8').read()
soup = BeautifulSoup(html_content, 'lxml')
for script in soup.find_all('script'):
    if script.string and 'window.model =' in script.string:
        raw = script.string.strip()
        start = raw.find('window.model =') + len('window.model =')
        jstr = raw[start:]
        if jstr.endswith(';'): jstr = jstr[:-1]
        try:
            data = json.loads(jstr)
            print("KEYS:", data.keys())
            if 'product' in data:
                print("PRODUCT KEYS:", data['product'].keys())
                if 'otherSellers' in data['product']:
                    print("OTHER SELLERS:", len(data['product']['otherSellers']))
                else:
                    print("No otherSellers in product")
        except Exception as e:
            print("Error parsing:", e)
