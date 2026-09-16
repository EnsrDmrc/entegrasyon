from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import sys

def debug_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml",
    }
    resp = requests.get(url, headers=headers, impersonate="chrome110", timeout=15.0)
    soup = BeautifulSoup(resp.text, 'lxml')
    for script in soup.find_all('script'):
        if script.string and 'window.model = ' in script.string:
            raw = script.string.strip()
            start = raw.find('window.model = ') + len('window.model = ')
            jstr = raw[start:]
            if jstr.endswith(';'): jstr = jstr[:-1]
            data = json.loads(jstr)
            with open("model.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Dumped window.model to model.json")
            break
            
if __name__ == "__main__":
    debug_url("https://www.n11.com/urun/3m-temflex-1300e-izole-bant-100-adet-siyah-36522851?magaza=saygingrup")
