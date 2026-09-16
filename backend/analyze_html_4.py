from bs4 import BeautifulSoup
import re

with open("n11_test.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

print("Looking for 1350 or 1.350...")
texts = soup.find_all(string=re.compile(r'1\.?350'))
for t in texts:
    parent = t.find_parent()
    if parent:
        print("Found in tag:", parent.name, "Class:", parent.get('class'))
        print("Text:", parent.text.strip())
        print("HTML:", str(parent))
        print("---")
        
print("Looking for SEPETTE...")
texts = soup.find_all(string=re.compile(r'SEPETTE', re.IGNORECASE))
for t in texts:
    parent = t.find_parent()
    if parent:
        print("Found SEPETTE in tag:", parent.name, "Class:", parent.get('class'))
        print("Text:", parent.text.strip())
