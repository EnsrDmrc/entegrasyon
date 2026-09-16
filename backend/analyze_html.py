from bs4 import BeautifulSoup
import json

with open("n11_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

print("1. PRIMARY SELLER INFO")
price_container = soup.select_one('.unf-p-detail-price, .priceContainer')
if price_container:
    print(price_container.text.strip()[:200])

print("\n2. OTHER SELLERS")
other_sellers = soup.select('.other-sellers-container .seller-list-item, .other-sellers .seller-item, li.seller')
if not other_sellers:
    # Try finding div with text "Diğer Mağazalar"
    divs = soup.find_all('div')
    for d in divs:
        if d.text and "Diğer Mağazalar" in d.text and len(d.text) < 200:
            print("Found heading:", d.text)
            
# Let's just find the A tag with KoStore
k = soup.find("a", href=lambda h: h and "kostore" in h.lower())
if k:
    # Get its parent container
    container = k.find_parent("div", class_=lambda c: c and "Item" in c)
    if not container:
        container = k.find_parent("div")
        if container:
            container = container.find_parent("div")
    if container:
        print("KoStore container class:", container.get('class'))
        print("KoStore text:", container.text.strip())

print("\n3. window.model check")
for script in soup.find_all('script'):
    if script.string and 'window.model = ' in script.string:
        raw_text = script.string.strip()
        start_idx = raw_text.find('window.model = ') + len('window.model = ')
        json_str = raw_text[start_idx:]
        if json_str.endswith(';'): json_str = json_str[:-1]
        data = json.loads(json_str)
        # Check if otherSellers is in product
        p = data.get("product", {})
        print("Other keys in product:", [k for k in p.keys() if "seller" in k.lower()])
        break
