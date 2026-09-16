import json
import re
from bs4 import BeautifulSoup

with open("n11_test.html", "r", encoding="utf-8") as f:
    html = f.read()

for script in BeautifulSoup(html, 'lxml').find_all('script'):
    if script.string and 'window.model = ' in script.string:
        raw = script.string.strip()
        idx = raw.find('window.model = ') + len('window.model = ')
        json_str = raw[idx:]
        if json_str.endswith(';'): json_str = json_str[:-1]
        
        data = json.loads(json_str)
        
        # search for 1350 in values recursively
        def search_dict(d, path=""):
            if isinstance(d, dict):
                for k, v in d.items():
                    search_dict(v, path + f".{k}")
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    search_dict(v, path + f"[{i}]")
            else:
                s = str(d).replace(" ", "")
                if "1350" in s or "1.350" in s:
                    print(f"FOUND 1350 AT: {path} = {d}")
                if "1228" in s or "1.228" in s:
                    print(f"FOUND 1228 AT: {path} = {d}")
                    
        search_dict(data, "window.model")
        break
