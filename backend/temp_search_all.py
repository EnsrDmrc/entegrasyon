import json
from curl_cffi import requests
url = 'https://www.n11.com/urun/3m-temflex-1300e-izole-bant-100-adet-siyah-36522851'
headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
r = requests.get(url, headers=headers, impersonate='chrome110')
from bs4 import BeautifulSoup
soup = BeautifulSoup(r.text, 'lxml')
for script in soup.find_all('script'):
    if script.string and 'window.model = ' in script.string:
        raw = script.string.strip()
        start = raw.find('window.model = ') + len('window.model = ')
        jstr = raw[start:]
        if jstr.endswith(';'): jstr = jstr[:-1]
        data = json.loads(jstr)
        if 'searchResults' in data:
            results = data.get('searchResults', [])
            for item in results:
                seller = item.get('sellerNickName')
                print(f"SELLER: {seller}, PRICE: {item.get('price')}, DISPLAY: {item.get('displayPrice')}, ID: {item.get('id')}")
