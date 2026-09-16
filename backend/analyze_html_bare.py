import json
from bs4 import BeautifulSoup

with open("n11_test_bare.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

for script in soup.find_all('script'):
    if script.string and 'window.model = ' in script.string:
        raw_text = script.string.strip()
        start_idx = raw_text.find('window.model = ') + len('window.model = ')
        json_str = raw_text[start_idx:]
        if json_str.endswith(';'): json_str = json_str[:-1]
        data = json.loads(json_str)
        
        p = data.get("product", {})
        print("oldPrice:", p.get("oldPrice"))
        print("price:", p.get("price"))
        print("displayPrice:", p.get("displayPrice"))
        print("discountRate:", p.get("discountRate"))
        print("instantDiscountPercentage:", p.get("instantDiscountPercentage"))
        print("instantDiscountPrice:", p.get("instantDiscountPrice"))
        print("hasInstantDiscount:", p.get("hasInstantDiscount"))
        
        # Check other sellers in product
        print("sellerShopBundles:", p.get("sellerShopBundles"))
        
        # Is searchResults here?
        print("searchResults present:", "searchResults" in data)
        break
