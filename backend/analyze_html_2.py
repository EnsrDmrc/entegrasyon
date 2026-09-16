from bs4 import BeautifulSoup

with open("n11_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

sellers_div = soup.find_all("div", class_="unifiedProductPrice")
for div in sellers_div:
    print("HTML:", str(div))
    print("---")
