import cloudscraper
import json
from bs4 import BeautifulSoup

url = "https://www.n11.com/urun/yildiz-iki-agiz-anahtar-14x15-130617729?magaza=saygingrup"
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
resp = scraper.get(url)

print("Status:", resp.status_code)

soup = BeautifulSoup(resp.text, 'lxml')

# Diğer satıcıları bulalım
other_sellers = soup.select('.other-sellers .seller-item, .sellerList .sellerItem, .other-seller-item, li.seller, .other-sellers-container .seller')
print(f"Found {len(other_sellers)} other sellers using CSS selectors.")
for s in other_sellers:
    print(s.text.strip()[:100])

# HTML içinde KoStore kelimesini arayalım
import re
match = re.search(r'KoStore', resp.text, re.IGNORECASE)
if match:
    print("KoStore is in HTML! Let's find context.")
    idx = resp.text.find('KoStore')
    print("Context around KoStore:", resp.text[idx-200:idx+200])
else:
    print("KoStore NOT FOUND in HTML! N11 might load it dynamically via AJAX.")
