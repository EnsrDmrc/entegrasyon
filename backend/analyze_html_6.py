from bs4 import BeautifulSoup
import re

with open("n11_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

print("--- MAIN SELLER ---")
main_price = soup.select_one('.unf-p-detail-price, .priceContainer')
if main_price:
    print(main_price.text.strip().replace('\n', ' '))
    
old_price = soup.select_one('.oldPrice, del, .unf-price-old')
if old_price:
    print("Old price:", old_price.text.strip())
    
print("--- OTHER SELLERS ---")
other_sellers = soup.select('.unifiedProduct')
for s in other_sellers:
    name = s.select_one('.name')
    price = s.select_one('.priceDisplay, .price, .newPrice')
    if name and price:
        print(f"Seller: {name.text.strip()}, Price: {price.text.strip()}")
