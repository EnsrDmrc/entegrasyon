from curl_cffi import requests
import json
import re
from bs4 import BeautifulSoup

class N11Scraper:
    def __init__(self):
        pass
        
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
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            }
            resp = requests.get(url, headers=headers, impersonate="chrome110", timeout=15.0)
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
                                        
                                    # Görünen fiyat (Sepet fiyatı)
                                    cart_price_raw = item.get("displayPrice")
                                    if cart_price_raw is None:
                                        cart_price_raw = item.get("price")
                                        
                                    # Eski fiyat (İndirimsiz/Üstü çizili fiyat)
                                    base_price_raw = item.get("price")
                                    if item.get("oldPrice"):
                                        old_price_str = item.get("oldPrice").replace("TL", "").replace(".", "").replace(",", ".").strip()
                                        try:
                                            base_price_raw = float(old_price_str)
                                        except:
                                            pass
                                            
                                    def parse_price(p):
                                        if isinstance(p, (int, float)): return float(p)
                                        if isinstance(p, str):
                                            s = p.replace("TL", "").strip().replace(".", "").replace(",", ".")
                                            try: return float(s)
                                            except: return 0.0
                                        return 0.0
                                        
                                    cart_price = parse_price(cart_price_raw)
                                    base_price = parse_price(base_price_raw)
                                    
                                    # Eğer N11 platform indirimi varsa
                                    platform_discount = 0.0
                                    if base_price > 0 and cart_price < base_price:
                                        platform_discount = 1 - (cart_price / base_price)
                                        
                                    competitors.append({
                                        "seller_name": str(seller_name).strip(),
                                        "price": cart_price,  # Repricing için ana karşılaştırma ölçütü: sepet fiyatı
                                        "base_price": base_price,
                                        "platform_discount": platform_discount
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
