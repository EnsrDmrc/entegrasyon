import cloudscraper
import json
from bs4 import BeautifulSoup

url = "https://www.n11.com/urun/apple-iphone-13-128-gb-apple-turkiye-garantili-2115132"
scraper = cloudscraper.create_scraper()
resp = scraper.get(url)

soup = BeautifulSoup(resp.text, 'lxml')

for script in soup.find_all('script'):
    if script.string and 'window.model = ' in script.string:
        raw_text = script.string.strip()
        start_idx = raw_text.find('window.model = ') + len('window.model = ')
        json_str = raw_text[start_idx:]
        if json_str.endswith(';'): json_str = json_str[:-1]
            
        data = json.loads(json_str)
        if "searchResults" in data:
            results = data["searchResults"]
            print(f"Type of searchResults: {type(results)}")
            if isinstance(results, dict):
                print(f"Keys in searchResults: {results.keys()}")
            elif isinstance(results, list):
                print(f"List length: {len(results)}")
                if len(results) > 0:
                    print(f"First item type: {type(results[0])}")
                    if isinstance(results[0], dict):
                        print(f"First item keys: {results[0].keys()}")
                        print(f"First item snippet: {str(results[0])[:200]}")
        break
