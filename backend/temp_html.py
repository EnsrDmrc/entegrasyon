from curl_cffi import requests
url = 'https://www.n11.com/urun/3m-temflex-1300e-izole-bant-100-adet-siyah-12598962'
r = requests.get(url, impersonate='chrome110')
if 'Tüm Satıcılar' in r.text or 'tüm satıcılar' in r.text.lower():
    print("HAS ALL SELLERS BUTTON")
else:
    print("NO ALL SELLERS BUTTON")
