from curl_cffi import requests

def test_n11():
    url = "https://www.n11.com/urun/yildiz-iki-agiz-anahtar-14x15-130617729?magaza=saygingrup"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome110", timeout=10)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            if "saygingrup" in r.text or "saygıngrup" in r.text.lower():
                print("SUCCESS: Found store name in HTML")
            else:
                print("FAILED: Store name not found in HTML")
        else:
            print("FAILED: Status code not 200")
            print(r.text[:500])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_n11()
