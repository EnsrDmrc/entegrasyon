from bs4 import BeautifulSoup
import re

with open("n11_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

print("Looking for 1228...")
texts = soup.find_all(string=re.compile(r'1\.?228'))
for t in texts:
    parent = t.find_parent()
    if parent:
        print("Found in tag:", parent.name, "Class:", parent.get('class'))
        print("Text:", parent.text.strip())
        print("---")
