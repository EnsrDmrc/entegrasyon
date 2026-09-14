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
                                        
                                    # Fiyat string ise float'a çevir (örn: "1.228,50 TL")
                                    if isinstance(price, str):
                                        price_str = price.replace("TL", "").strip()
                                        price_str = price_str.replace(".", "").replace(",", ".")
                                        try:
                                            price = float(price_str)
                                        except:
                                            price = 0.0
                                            
                                    discount_rate = item.get("discountRate", 0)
                                    instant_discount = item.get("instantDiscountPercentage", 0)
                                    
                                    total_discount = max(float(discount_rate or 0), float(instant_discount or 0))
                                    
                                    competitors.append({
                                        "seller_name": str(seller_name).strip(),
                                        "price": float(price),
                                        "discount_rate": total_discount
                                    })
                        elif "product" in data and "seller" in data["product"]:
                            # Tek satıcılı sayfa (Rakipler yok)
                            p = data["product"]
                            seller_name = p["seller"].get("nickName")
                            price = p.get("displayPrice") or p.get("price")
                            
                            if isinstance(price, str):
                                price_str = price.replace("TL", "").strip()
                                price_str = price_str.replace(".", "").replace(",", ".")
                                try:
                                    price = float(price_str)
                                except:
                                    price = 0.0
                                    
                            discount_rate = p.get("discountRate", 0)
                            competitors.append({
                                "seller_name": str(seller_name).strip() if seller_name else "Unknown",
                                "price": float(price),
                                "discount_rate": float(discount_rate or 0)
                            })
                        break
                    except Exception as e:
                        print(f"[N11Scraper] JSON Parse hatası: {e}")
            
            # HTML üzerinden diğer satıcıları kontrol et (Product Detail sayfasında window.model'de gelmeyebilir)
            other_sellers = soup.select('.unifiedProduct.pdpSidebarUnification, .other-sellers-container .seller-list-item, .other-sellers .seller-item, li.seller')
            for s in other_sellers:
                name_elem = s.select_one('.name')
                price_elem = s.select_one('.priceDisplay, .price, .newPrice, ins')
                
                if name_elem and price_elem:
                    s_name = name_elem.text.strip()
                    p_text = price_elem.text.strip()
                    
                    # Eğer satıcı zaten eklenmişse atla
                    if any(c["seller_name"].lower() == s_name.lower() for c in competitors):
                        continue
                        
                    price_val = 0.0
                    price_str = p_text.replace("TL", "").strip()
                    price_str = price_str.replace(".", "").replace(",", ".")
                    try:
                        price_val = float(price_str)
                    except:
                        pass
                        
                    if price_val > 0:
                        competitors.append({
                            "seller_name": s_name,
                            "price": price_val,
                            "discount_rate": 0.0
                        })

            # HTML'den ana satıcının asıl liste fiyatını (oldPrice) veya indirimini de bulmayı deneyebiliriz
            main_old_price_elem = soup.select_one('.unf-price-old, del, .oldPrice')
            if main_old_price_elem and len(competitors) > 0:
                old_p_text = main_old_price_elem.text.strip().replace("TL", "").strip().replace(".", "").replace(",", ".")
                try:
                    old_p_val = float(old_p_text)
                    # Ana satıcıyı bul (genellikle ilk sıradaki veya saygingrup olan)
                    # Basitlik açısından, eğer en düşük fiyat ana satıcıysa ve discount_rate 0 ise, oldPrice'a göre indirim hesapla.
                    pass 
                except:
                    pass
                        
            # Fiyata göre küçükten büyüğe sırala
            competitors = sorted(competitors, key=lambda x: x["price"])
            return competitors
            
        except Exception as e:
            print(f"[N11Scraper] Hata oluştu: {e}")
            return []
