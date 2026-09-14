import cloudscraper
import json
import re
from bs4 import BeautifulSoup

class N11Scraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
    def get_competitors(self, url: str) -> list:
        """
        Verilen N11 ürün sayfasından rakipleri ve fiyatlarını çeker.
        Dönüş formatı:
        [
            {
                "seller_name": "SaticiAdi",
                "price": 1250.50,
                "discount_rate": 10  # Yüzde 10 indirim
            },
            ...
        ]
        """
        try:
            resp = self.scraper.get(url, timeout=15.0)
            if resp.status_code != 200:
                print(f"[N11Scraper] HTTP Hatası: {resp.status_code} - URL: {url}")
                return []
                
            soup = BeautifulSoup(resp.text, 'lxml')
            competitors = []
            
            # window.model state içinden veriyi çıkar
            for script in soup.find_all('script'):
                if script.string and 'window.model = ' in script.string:
                    raw_text = script.string.strip()
                    start_idx = raw_text.find('window.model = ') + len('window.model = ')
                    json_str = raw_text[start_idx:]
                    if json_str.endswith(';'): 
                        json_str = json_str[:-1]
                        
                    try:
                        data = json.loads(json_str)
                        if "searchResults" in data:
                            results = data["searchResults"]
                            if isinstance(results, list):
                                for item in results:
                                    seller_name = item.get("sellerNickName")
                                    if not seller_name:
                                        continue
                                        
                                    price = item.get("displayPrice")
                                    if price is None:
                                        price = item.get("price")
                                        
                                    discount_rate = item.get("discountRate", 0)
                                    instant_discount = item.get("instantDiscountPercentage", 0)
                                    
                                    # En yüksek indirim oranını al (N11 destekli indirim genelde instantDiscountPercentage olur)
                                    total_discount = max(float(discount_rate or 0), float(instant_discount or 0))
                                    
                                    competitors.append({
                                        "seller_name": str(seller_name).strip(),
                                        "price": float(price),
                                        "discount_rate": total_discount
                                    })
                        break
                    except Exception as e:
                        print(f"[N11Scraper] JSON Parse hatası: {e}")
                        
            # Fiyata göre küçükten büyüğe sırala
            competitors = sorted(competitors, key=lambda x: x["price"])
            return competitors
            
        except Exception as e:
            print(f"[N11Scraper] Hata oluştu: {e}")
            return []
