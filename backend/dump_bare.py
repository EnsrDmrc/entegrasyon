import cloudscraper
import json

url = "https://www.n11.com/urun/yildiz-iki-agiz-anahtar-14x15-130617729"
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
resp = scraper.get(url)

with open("n11_test_bare.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
