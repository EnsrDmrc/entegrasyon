import json
from curl_cffi import requests
url = 'https://www.n11.com/arama?q=3M+Temflex+1300E+İzole+Bant+100+Adet+Siyah'
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
        results = data.get('searchResults', [])
        for item in results:
            seller = item.get('sellerNickName')
            if seller and ('goztepe' in seller.lower()):
                print(f"SELLER: {seller}")
                print(f"PRICE: {item.get('price')}")
                print(f"URL: {item.get('url') or item.get('productUrl')}")
                print('---')
