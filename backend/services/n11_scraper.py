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
            }
            
            # Parametreleri temizle (?magaza= vs gibi) aksi takdirde N11 o mağazayı ana satıcı yapar ve en ucuzu gizler
            # Do not strip query parameters, as they are needed for variants (e.g. ?secenekler=...)
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
                    idx = raw_text.find('window.model = ')
                    start_idx = raw_text.find('{', idx)
                    open_brackets = 0
                    end_idx = -1
                    for i in range(start_idx, len(raw_text)):
                        if raw_text[i] == '{': open_brackets += 1
                        elif raw_text[i] == '}':
                            open_brackets -= 1
                            if open_brackets == 0:
                                end_idx = i + 1
                                break
                    if end_idx != -1:
                        json_str = raw_text[start_idx:end_idx]
                        
                    try:
                        data = json.loads(json_str)
                        is_search_url = '/arama' in url or '/kampanya' in url
                        
                        if is_search_url and "searchResults" in data:
                            results = data["searchResults"]
                            if isinstance(results, list):
                                for item in results:
                                    seller_name = item.get("sellerNickName")
                                    if not seller_name:
                                        continue
                                        
                                    cart_price_raw = item.get("displayPrice")
                                    if cart_price_raw is None:
                                        cart_price_raw = item.get("price")
                                        
                                    base_price_raw = item.get("price")
                                    if item.get("oldPrice"):
                                        old_price_str = str(item.get("oldPrice")).replace("TL", "").replace(".", "").replace(",", ".").strip()
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
                                    
                                    instant_discount_raw = item.get("instantDiscountPercentage")
                                    if instant_discount_raw:
                                        if isinstance(instant_discount_raw, str):
                                            idp_str = instant_discount_raw.replace("%", "").strip()
                                            try:
                                                idp_val = float(idp_str) / 100.0
                                                cart_price = cart_price * (1.0 - idp_val)
                                            except:
                                                pass
                                        elif isinstance(instant_discount_raw, (int, float)):
                                            cart_price = cart_price * (1.0 - (float(instant_discount_raw) / 100.0))
                                            
                                    platform_discount = 0.0
                                    if base_price > 0 and cart_price < base_price:
                                        platform_discount = 1 - (cart_price / base_price)
                                        
                                    stock_val = 0
                                    if item.get("stockAmount"):
                                        stock_val = int(item.get("stockAmount"))
                                    elif item.get("quantity"):
                                        stock_val = int(item.get("quantity"))
                                    elif item.get("maxQuantity"):
                                        stock_val = int(item.get("maxQuantity"))
                                        
                                    competitors.append({
                                        "seller_name": str(seller_name).strip(),
                                        "price": cart_price,
                                        "base_price": base_price,
                                        "platform_discount": platform_discount,
                                        "stock": stock_val
                                    })
                                    
                        elif not is_search_url and ("product" in data.get("data", {}) or "product" in data):
                            # N11 yeni (data.product) veya eski (product) yapısı
                            p = data.get("data", {}).get("product", data.get("product", {}))
                            seller_name = p.get("seller", {}).get("nickName") if p.get("seller") else None
                            
                            def parse_price(pr):
                                if isinstance(pr, (int, float)): return float(pr)
                                if isinstance(pr, str):
                                    s = pr.replace("TL", "").strip().replace(".", "").replace(",", ".")
                                    try: return float(s)
                                    except: return 0.0
                                return 0.0
                                
                            def parse_product_discount(prod_obj):
                                base_price = parse_price(prod_obj.get("price"))
                                cart_price = parse_price(prod_obj.get("displayPrice") or prod_obj.get("price"))
                                
                                # displayPrice genellikle sepetteki son fiyattır. Eğer displayPrice yoksa
                                # ve campaignPrice varsa onu kullanırız.
                                campaign_price_raw = prod_obj.get("campaignPrice")
                                if campaign_price_raw:
                                    try:
                                        cmp_val = float(str(campaign_price_raw).replace("TL", "").replace(".", "").replace(",", ".").strip())
                                        if cmp_val > 0 and cmp_val < cart_price:
                                            cart_price = cmp_val
                                    except: pass
                                
                                return cart_price, base_price, 0.0
                                
                            # Ana ürünü ekle (Eğer satıcı varsa)
                            if seller_name:
                                cart_price, base_price, disc_rate = parse_product_discount(p)
                                stock_val = int(p.get("stockAmount", p.get("quantity", p.get("maxQuantity", 0))))
                                competitors.append({
                                    "seller_name": str(seller_name).strip(),
                                    "price": float(cart_price),
                                    "discount_rate": disc_rate,
                                    "stock": stock_val
                                })
                                
                            # Diğer satıcıları ekle (unificationInfo veya pdpModel yapısı)
                            other_sellers_list = data.get("unificationInfo", {}).get("otherSellersProducts")
                            if other_sellers_list is None:
                                other_sellers_list = data.get("pdpModel", {}).get("otherSellers", [])
                                
                            if other_sellers_list:
                                for s in other_sellers_list:
                                    s_name = s.get("sellerName")
                                    if not s_name: continue
                                    s_cart, s_base, s_disc = parse_product_discount(s)
                                    s_stock = int(s.get("stockAmount", s.get("quantity", s.get("maxQuantity", 0))))
                                    competitors.append({
                                        "seller_name": str(s_name).strip(),
                                        "price": float(s_cart),
                                        "discount_rate": s_disc,
                                        "stock": s_stock
                                    })
                        break
                    except Exception as e:
                        print(f"[N11Scraper] JSON Parse hatası: {e}")
            
            # HTML üzerinden diğer satıcıları kontrol et (Product Detail sayfasında window.model'de gelmeyebilir)
            other_sellers = soup.select('.unifiedProduct.pdpSidebarUnification, .other-sellers-container .seller-list-item, .other-sellers .seller-item, li.seller, .seller-list-item, .seller-item, .seller-container, .unf-p-seller-list li')
            for s in other_sellers:
                name_elem = s.select_one('.name, .seller-name, .store-name, .s-name, h3, a.title')
                # DOM sırasına göre değil, önem sırasına göre seçmek için 'or' kullanıyoruz.
                # N11 bazen <div class="price"> SEPETTE </div> veriyor, <div class="priceDisplay"> 1.046 TL </div>
                price_elem = s.select_one('.priceDisplay') or s.select_one('.newPrice') or s.select_one('ins') or s.select_one('.new-price') or s.select_one('.price') or s.select_one('.s-price')
                
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
                            "discount_rate": 0.0,
                            "stock": 0 # HTML parsing'den stock zor çıkar
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
