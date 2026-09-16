import asyncio
from services.n11_scraper import N11Scraper

url = 'https://www.n11.com/arama?q=3m+temflex+1300e+siyah+100'
scraper = N11Scraper()
comps = scraper.get_competitors(url)
print('Scraped competitors:')
for idx, c in enumerate(comps):
    print(f"{idx}. {c['seller_name']} - {c['price']}")
