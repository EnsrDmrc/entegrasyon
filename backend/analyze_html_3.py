from bs4 import BeautifulSoup

with open("n11_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

sellers_div = soup.find_all("div", class_="unifiedProductPrice")
if sellers_div:
    for div in sellers_div:
        # Find the parent that contains both name and price
        parent = div.find_parent("li")
        if not parent:
            parent = div.find_parent("div", class_=lambda x: x and "seller" in x.lower())
        
        if parent:
            print("--- PARENT HTML ---")
            print(str(parent))
