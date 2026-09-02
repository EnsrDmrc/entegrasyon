from abc import ABC, abstractmethod

class MarketplaceAdapter(ABC):
    
    @abstractmethod
    def update_product(self, sku: str, new_price: float = None, new_stock: int = None) -> bool:
        pass
        
    @abstractmethod
    def get_product_details(self, sku: str) -> dict:
        pass


import httpx

class ShopifyAdapter(MarketplaceAdapter):
    def __init__(self, api_key: str, store_url: str):
        self.api_key = api_key
        # Varsayılan store_url "magaza.myshopify.com" şeklinde gelmeli
        self.store_url = store_url.replace("https://", "").replace("http://", "").strip("/")
        self.base_url = f"https://{self.store_url}/admin/api/2024-01"
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.api_key
        }
        
    def update_product(self, sku: str, new_price: float = None, new_stock: int = None) -> bool:
        try:
            with httpx.Client() as client:
                variant_id = None
                inventory_item_id = None
                
                # Eşleştirme Mantığı
                if sku.startswith("SHOP-"):
                    var_id = sku.replace("SHOP-", "")
                    resp = client.get(f"{self.base_url}/variants/{var_id}.json", headers=self.headers)
                    if resp.status_code == 200:
                        var_data = resp.json().get("variant", {})
                        variant_id = var_data.get("id")
                        inventory_item_id = var_data.get("inventory_item_id")
                else:
                    url = f"{self.base_url}/products.json?limit=250"
                    found = False
                    while url and not found:
                        resp = client.get(url, headers=self.headers)
                        if resp.status_code != 200:
                            break
                        data = resp.json()
                        for prod in data.get("products", []):
                            for var in prod.get("variants", []):
                                if var.get("sku") == sku:
                                    variant_id = var.get("id")
                                    inventory_item_id = var.get("inventory_item_id")
                                    found = True
                                    break
                            if found: break
                        if "next" in resp.links:
                            url = resp.links["next"]["url"]
                        else:
                            url = None

                if not variant_id:
                    print(f"[Shopify] {sku} SKU'lu varyant bulunamadı.")
                    return False
                
                success = True
                
                # 1. Fiyat Güncellemesi
                if new_price is not None:
                    payload = {"variant": {"id": variant_id, "price": str(new_price)}}
                    res = client.put(f"{self.base_url}/variants/{variant_id}.json", headers=self.headers, json=payload)
                    if res.status_code not in (200, 201):
                        print(f"[Shopify] Fiyat güncellenemedi: {res.text}")
                        success = False
                        
                # 2. Stok Güncellemesi
                if new_stock is not None and inventory_item_id:
                    loc_res = client.get(f"{self.base_url}/locations.json", headers=self.headers)
                    if loc_res.status_code == 200 and loc_res.json().get("locations"):
                        location_id = loc_res.json()["locations"][0]["id"]
                        inv_payload = {
                            "location_id": location_id,
                            "inventory_item_id": inventory_item_id,
                            "available": new_stock
                        }
                        inv_res = client.post(f"{self.base_url}/inventory_levels/set.json", headers=self.headers, json=inv_payload)
                        if inv_res.status_code not in (200, 201):
                            print(f"[Shopify] Stok güncellenemedi: {inv_res.text}")
                            success = False
                    else:
                        print("[Shopify] Lokasyon bulunamadı.")
                        success = False
                        
                return success
        except Exception as e:
            print(f"[Shopify] API Hatası: {e}")
            return False

    def get_product_details(self, sku: str) -> dict:
        try:
            with httpx.Client() as client:
                # Query products by SKU using GraphQL or just find the variant with that SKU in REST
                response = client.get(f"{self.base_url}/products.json", headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    for product in data.get("products", []):
                        for variant in product.get("variants", []):
                            if variant.get("sku") == sku:
                                images = [img.get("src") for img in product.get("images", [])] if product.get("images") else []
                                return {
                                    "sku": sku, 
                                    "name": product.get("title", ""), 
                                    "description": product.get("body_html", ""),
                                    "price": float(variant.get("price", 0.0)),
                                    "images": images,
                                    "category_name": product.get("product_type", ""),
                                    "brand_name": product.get("vendor", "")
                                }
        except Exception as e:
            print(f"[Shopify] API Hatası: {e}")
        return {"sku": sku, "name": "Bilinmeyen Ürün", "price": 0.0, "category_name": "", "brand_name": ""}

    def fetch_all_products(self) -> list:
        """Shopify'dan tüm ürünleri ve varyantları çeker (sayfalandırma destekli)."""
        fetched_variants = []
        try:
            with httpx.Client() as client:
                url = f"{self.base_url}/products.json?limit=250"
                while url:
                    response = client.get(url, headers=self.headers)
                    if response.status_code != 200:
                        print(f"[Shopify] API Hatası: {response.text}")
                        break
                    
                    data = response.json()
                    products = data.get("products", [])
                    for prod in products:
                        title = prod.get("title", "")
                        for var in prod.get("variants", []):
                            # SKU yoksa, Shopify'ın varyant ID'sini kullanarak otomatik bir SKU oluştur.
                            sku = var.get("sku")
                            if not sku:
                                sku = f"SHOP-{var.get('id')}"
                                
                            price = float(var.get("price", 0.0))
                            qty = int(var.get("inventory_quantity", 0))
                            
                            fetched_variants.append({
                                "sku": sku,
                                "name": f"{title} - {var.get('title', '')}".strip(" -"),
                                "price": price,
                                "quantity": qty,
                                "marketplace": "shopify"
                            })
                    
                    # Sonraki sayfa var mı kontrol et (Link header'ı üzerinden cursor pagination)
                    if "next" in response.links:
                        url = response.links["next"]["url"]
                    else:
                        url = None
                        
        except Exception as e:
            print(f"[Shopify Sync Hatası]: {e}")
            
        return fetched_variants

    def fetch_orders(self) -> list:
        """Shopify'dan siparişleri çeker (sayfalandırma destekli)."""
        fetched_orders = []
        try:
            with httpx.Client() as client:
                url = f"{self.base_url}/orders.json?status=any&limit=250"
                while url:
                    response = client.get(url, headers=self.headers)
                    if response.status_code != 200:
                        print(f"[Shopify] API Hatası: {response.text}")
                        break
                    
                    data = response.json()
                    orders = data.get("orders", [])
                    for ord_data in orders:
                        order_id = str(ord_data.get("id", ""))
                        order_number = str(ord_data.get("order_number", order_id))
                        customer = ord_data.get("customer", {})
                        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
                        total_price = float(ord_data.get("total_price", 0.0))
                        status = ord_data.get("financial_status", "pending")
                        order_date = ord_data.get("created_at")
                        
                        items = []
                        for line in ord_data.get("line_items", []):
                            sku = line.get("sku")
                            if not sku:
                                sku = f"SHOP-{line.get('variant_id')}"
                                
                            items.append({
                                "product_sku": sku,
                                "product_name": line.get("title", ""),
                                "quantity": int(line.get("quantity", 1)),
                                "price": float(line.get("price", 0.0))
                            })
                            
                        fetched_orders.append({
                            "order_number": order_number,
                            "customer_name": customer_name,
                            "total_price": total_price,
                            "status": status,
                            "order_date": order_date,
                            "items": items
                        })
                    
                    if "next" in response.links:
                        url = response.links["next"]["url"]
                    else:
                        url = None
                        
        except Exception as e:
            print(f"[Shopify Order Sync Hatası]: {e}")
            
        return fetched_orders

import zeep
from zeep import Client, Settings

class N11Adapter(MarketplaceAdapter):
    def __init__(self, api_key: str, api_secret: str):
        self.auth = {
            'appKey': api_key.strip(),
            'appSecret': api_secret.strip()
        }
        settings = Settings(strict=False, xsd_ignore_sequence_order=True)
        self.product_client = zeep.Client('https://api.n11.com/ws/ProductService.wsdl', settings=settings)
        self.order_client = zeep.Client('https://api.n11.com/ws/OrderService.wsdl', settings=settings)
        
    def get_product_details(self, sku: str) -> dict:
        try:
            from zeep.helpers import serialize_object
            res = self.product_client.service.GetProductBySellerCode(auth=self.auth, sellerCode=sku)
            if res.result.status == "failure":
                raise Exception(f"N11 Ürün detayı çekilemedi: {res.result.errorMessage}")
            
            prod = serialize_object(res.product)
            if not isinstance(prod, dict):
                prod = {}
                
            # N11'den gelen veriyi standardize edelim
            images = []
            if prod.get('images') and isinstance(prod['images'], dict) and prod['images'].get('image'):
                image_list = prod['images']['image']
                if not isinstance(image_list, list):
                    image_list = [image_list]
                for img in image_list:
                    if isinstance(img, dict) and img.get('url'):
                        images.append(img['url'])
                        
            description = prod.get('description', '')
                
            brand_name = ""
            if prod.get('attributes') and isinstance(prod['attributes'], dict) and prod['attributes'].get('attribute'):
                attr_list = prod['attributes']['attribute']
                if not isinstance(attr_list, list):
                    attr_list = [attr_list]
                for attr in attr_list:
                    if isinstance(attr, dict) and attr.get('name', '').lower() == 'marka':
                        brand_name = attr.get('value', '')
                        break
                        
            cat_obj = prod.get('category') or {}
            category_id = cat_obj.get('id')
            category_name = cat_obj.get('name') or cat_obj.get('fullName') or ""
                
            return {
                "sku": sku,
                "name": prod.get('title', ''),
                "description": description,
                "price": float(prod.get('price', 0.0)) if prod.get('price') else 0.0,
                "images": images,
                "category_id": category_id,
                "category_name": category_name,
                "brand_name": brand_name
            }
        except Exception as e:
            raise Exception(f"N11'den {sku} kodlu ürün detayları alınırken hata oluştu: {str(e)}")
            
    def fetch_all_products(self) -> list:
        fetched_variants = []
        try:
            current_page = 0
            page_size = 100
            total_pages = 1
            
            while current_page <= total_pages:
                paging = {'currentPage': current_page, 'pageSize': page_size}
                res = self.product_client.service.GetProductList(auth=self.auth, pagingData=paging)
                
                if res.result.status == "failure":
                    raise Exception(f"N11 API Hatası: {res.result.errorMessage}")
                
                if current_page == 0 and res.pagingData:
                    total_pages = res.pagingData.pageCount - 1
                
                if not res.products or not res.products.product:
                    break
                    
                for prod in res.products.product:
                    sku = prod.productSellerCode
                    if not sku:
                        continue
                    
                    price = float(prod.price) if prod.price else 0.0
                    
                    qty = 0
                    if hasattr(prod, 'stockItems') and prod.stockItems:
                        if hasattr(prod.stockItems, 'stockItem') and prod.stockItems.stockItem:
                            for st in prod.stockItems.stockItem:
                                qty += (int(st.quantity) if st.quantity else 0)
                    
                    fetched_variants.append({
                        "sku": sku,
                        "name": prod.title or "",
                        "price": price,
                        "quantity": qty,
                        "marketplace": "n11"
                    })
                
                current_page += 1
                if current_page > total_pages:
                    break
        except Exception as e:
            print(f"[n11 Sync Hatası]: {e}")
            raise e
            
        return fetched_variants

    def fetch_orders(self) -> list:
        fetched_orders = []
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            
            # N11 WSDL şeması bazı alanların dictionary içinde mutlaka tanımlı olmasını bekler
            search_data = {
                'productId': '',
                'status': '', # Sadece 'New' değil tüm siparişleri çekmek için boş bırakıldı
                'buyerName': '',
                'orderNumber': '',
                'productSellerCode': '',
                'recipient': '',
                'sameDayDelivery': '',
                'period': {
                    'startDate': start_date.strftime('%d/%m/%Y 00:00'),
                    'endDate': end_date.strftime('%d/%m/%Y 23:59')
                },
                'sortForUpdateDate': True,
                'updateDateSortOrder': 'DESC'
            }
            
            all_summaries = []
            current_page = 0
            
            while True:
                paging = {'currentPage': current_page, 'pageSize': 100}
                res = self.order_client.service.OrderList(auth=self.auth, searchData=search_data, pagingData=paging)
                
                if res.result.status == "failure":
                    raise Exception(f"N11 API Hatası: {res.result.errorMessage}")
                
                if not res.orderList or not res.orderList.order:
                    break
                    
                all_summaries.extend(res.orderList.order)
                
                page_count = res.pagingData.pageCount if hasattr(res, 'pagingData') and hasattr(res.pagingData, 'pageCount') else 1
                current_page += 1
                if current_page >= page_count:
                    break
            
            # Güncellenme tarihine göre DESC sıralandığı için ilk sayfalarda en son güncellenenler gelir
            # Performans için sadece en son güncellenen 100 siparişi detaylı çekiyoruz
            latest_100_summaries = all_summaries[:100] if len(all_summaries) > 100 else all_summaries
            
            for ord_summary in latest_100_summaries:
                try:
                    # Siparişin detaylarını çekiyoruz çünkü OrderList sadece özet (summary) döner.
                    detail_res = self.order_client.service.OrderDetail(auth=self.auth, orderRequest={'id': ord_summary.id})
                    if detail_res.result.status == "failure" or not detail_res.orderDetail:
                        continue
                        
                    ord_data = detail_res.orderDetail
                    order_num = ord_data.orderNumber or str(ord_data.id)
                    buyer = ord_data.buyer.fullName if hasattr(ord_data, 'buyer') and ord_data.buyer else "N11 Müşteri"
                    
                    status_raw = str(ord_data.status) if hasattr(ord_data, 'status') else "1"
                    status_map = {
                        "1": "Yeni Sipariş",
                        "2": "Onaylandı",
                        "3": "Reddedildi",
                        "4": "Kargolandı",
                        "5": "Teslim Edildi",
                        "6": "Tamamlandı",
                        "7": "İade Edildi",
                        "8": "İptal Edildi"
                    }
                    status = status_map.get(status_raw, status_raw)
                    
                    date_str = str(ord_data.createDate) if hasattr(ord_data, 'createDate') and ord_data.createDate else None
                    
                    items = []
                    total_price = 0.0
                    if hasattr(ord_data, 'itemList') and ord_data.itemList and hasattr(ord_data.itemList, 'item') and ord_data.itemList.item:
                        for item in ord_data.itemList.item:
                            sku = item.productSellerCode or "N11-NO-SKU"
                            title = item.productName or ""
                            qty = int(item.quantity) if item.quantity else 1
                            price = float(item.price) if item.price else 0.0
                            total_price += price * qty
                            
                            items.append({
                                "product_sku": sku,
                                "product_name": title,
                                "quantity": qty,
                                "price": price
                            })
                    
                    if not items:
                        continue
                        
                    fetched_orders.append({
                        "order_number": order_num,
                        "customer_name": buyer,
                        "total_price": total_price,
                        "status": str(status),
                        "order_date": date_str,
                        "items": items
                    })
                except Exception as e:
                    print(f"Failed to fetch details for order {ord_summary.id}: {e}")
                    continue
        except Exception as e:
            print(f"[n11 Order Sync Hatası]: {e}")
            raise e
            
        return fetched_orders

    def update_product(self, sku: str, new_price: float=None, new_stock: int=None) -> bool:
        success = True
        try:
            import httpx
            
            headers = {
                "appkey": self.auth["appKey"],
                "appsecret": self.auth["appSecret"],
                "Content-Type": "application/json"
            }
            
            sku_data = {"stockCode": sku}
            if new_price is not None:
                sku_data["salePrice"] = float(new_price)
                sku_data["listPrice"] = float(new_price)
            if new_stock is not None:
                sku_data["quantity"] = int(new_stock)
                
            payload = {
                "payload": {
                    "integrator": "Entegrasyon",
                    "skus": [sku_data]
                }
            }
            
            with httpx.Client() as client:
                res = client.post(
                    "https://api.n11.com/ms/product/tasks/price-stock-update",
                    headers=headers,
                    json=payload
                )
                
                if res.status_code not in (200, 201, 202):
                    print(f"[N11] Stok/Fiyat güncellenemedi ({sku}): {res.text}")
                    success = False
                else:
                    data = res.json()
                    # Genellikle 'taskId' döner
                    if not data.get("taskId") and data.get("result", {}).get("status") == "failure":
                        print(f"[N11] REST API Hatası ({sku}): {res.text}")
                        success = False
                        
        except Exception as e:
            print(f"[N11] Stok/Fiyat güncelleme isteği başarısız ({sku}): {e}")
            success = False
            
        return success

    def get_product_details(self, sku: str) -> dict:
        return {"sku": sku, "name": "Test Product n11", "price": 100.0}

import base64

class HepsiburadaAdapter(MarketplaceAdapter):
    def __init__(self, merchant_id: str, api_key: str, is_test: bool = False, user_agent: str = "saygingrup_dev"):
        self.merchant_id = merchant_id.strip()
        self.api_key = api_key.strip()
        self.is_test = is_test
        
        # Hepsiburada API'leri genellikle Basic Auth kullanır.
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {base64.b64encode(f'{self.merchant_id}:{self.api_key}'.encode()).decode()}",
            "User-Agent": user_agent
        }
        
        if self.is_test:
            self.base_url_listing = "https://listing-external-sit.hepsiburada.com/listings/merchantid"
            self.base_url_order = "https://oms-external-sit.hepsiburada.com/packages/merchantid"
        else:
            self.base_url_listing = "https://listing-external.hepsiburada.com/listings/merchantid"
            self.base_url_order = "https://oms-external.hepsiburada.com/packages/merchantid"
        
    def fetch_all_products(self) -> list:
        # Eski MOCK modunu devre dışı bırakıyoruz, artık gerçek SIT ortamı var
        
        fetched_variants = []
        try:
            with httpx.Client() as client:
                # Hepsiburada ürün çekme API'si (Örnek Endpoint)
                url = f"{self.base_url_listing}/{self.merchant_id}?offset=0&limit=100"
                response = client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    listings = data.get("listings", [])
                    for item in listings:
                        sku = item.get("merchantSku")
                        if not sku:
                            continue
                            
                        fetched_variants.append({
                            "sku": sku,
                            "name": item.get("hbSkuTitle", f"Hepsiburada Ürünü - {sku}"),
                            "price": float(item.get("price", 0.0)),
                            "quantity": int(item.get("availableInventory", 0)),
                            "marketplace": "hepsiburada"
                        })
                elif response.status_code in (401, 403):
                    print("[Hepsiburada] Yetkilendirme hatası (API Key veya Merchant ID geçersiz)")
                else:
                    print(f"[Hepsiburada] API Hatası: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[Hepsiburada Sync Hatası]: {e}")
            
        return fetched_variants

    def fetch_orders(self) -> list:
        fetched_orders = []
        try:
            with httpx.Client() as client:
                # Hepsiburada Sipariş Çekme API'si (Örnek Endpoint)
                url = f"{self.base_url_order}/{self.merchant_id}?status=Unpacked,Packed,Shipped"
                response = client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    orders_data = response.json()
                    for pkg in orders_data:
                        order_number = pkg.get("orderNumber") or pkg.get("packageNumber")
                        if not order_number: continue
                        
                        customer = pkg.get("deliveryAddress", {})
                        customer_name = customer.get("name", "Hepsiburada Müşterisi")
                        
                        items = []
                        total_price = 0.0
                        
                        for line in pkg.get("lineItems", []):
                            price = float(line.get("price", 0.0))
                            qty = int(line.get("quantity", 1))
                            total_price += price * qty
                            
                            items.append({
                                "product_sku": line.get("merchantSku", "HB-UNKNOWN"),
                                "product_name": line.get("productName", ""),
                                "quantity": qty,
                                "price": price
                            })
                            
                        # Statüyü eşleştir
                        raw_status = pkg.get("status", "Unpacked")
                        status_map = {
                            "Unpacked": "Yeni Sipariş",
                            "Packed": "Onaylandı",
                            "Shipped": "Kargolandı",
                            "Delivered": "Teslim Edildi",
                            "Cancelled": "İptal Edildi"
                        }
                        
                        fetched_orders.append({
                            "order_number": str(order_number),
                            "customer_name": customer_name,
                            "total_price": total_price,
                            "status": status_map.get(raw_status, raw_status),
                            "order_date": pkg.get("orderDate"),
                            "items": items
                        })
                elif response.status_code in (401, 403):
                    print("[Hepsiburada Order] Yetkilendirme hatası")
        except Exception as e:
            print(f"[Hepsiburada Order Sync Hatası]: {e}")
            
        return fetched_orders

    def update_product(self, sku: str, new_price: float = None, new_stock: int = None) -> bool:
        success = True
        try:
            with httpx.Client() as client:
                url = f"{self.base_url_listing}/{self.merchant_id}/inventory-and-price"
                
                payload = {
                    "listings": [
                        {
                            "merchantSku": sku
                        }
                    ]
                }
                
                if new_price is not None:
                    payload["listings"][0]["price"] = float(new_price)
                if new_stock is not None:
                    payload["listings"][0]["availableInventory"] = int(new_stock)
                    payload["listings"][0]["maximumPurchasableQuantity"] = max(1, min(int(new_stock), 10))
                    payload["listings"][0]["dispatchTime"] = 2
                    
                response = client.post(url, headers=self.headers, json=payload)
                
                if response.status_code not in (200, 201, 202):
                    print(f"[Hepsiburada] Stok/Fiyat güncellenemedi ({sku}): {response.text}")
                    return False, f"HTTP {response.status_code}: {response.text}"
                return True, response.text
        except Exception as e:
            print(f"[Hepsiburada] API Hatası: {e}")
            return False, str(e)
            
        return success, "Bilinmeyen durum"

    def get_product_details(self, sku: str) -> dict:
        return {"sku": sku, "name": "Hepsiburada Ürünü", "price": 0.0}

class TrendyolAdapter(MarketplaceAdapter):
    def __init__(self, supplier_id: str, api_key: str, api_secret: str):
        self.supplier_id = supplier_id.strip()
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        
        auth_string = f"{self.api_key}:{self.api_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_auth}",
            "User-Agent": "EntegrasyonApp/1.0"
        }
        
        self.base_url = "https://api.trendyol.com/sapigw/suppliers"
        
    def fetch_all_products(self) -> list:
        # TEST (MOCK) MODU
        if self.supplier_id.lower() == "test":
            return [
                {"sku": "TY-TEST-001", "name": "Trendyol Test Ürünü 1", "price": 120.0, "quantity": 50, "marketplace": "trendyol"},
                {"sku": "TY-TEST-002", "name": "Trendyol Test Ürünü 2", "price": 85.50, "quantity": 10, "marketplace": "trendyol"}
            ]
            
        fetched_variants = []
        try:
            with httpx.Client() as client:
                # Trendyol ürün çekme API'si (Örnek Endpoint)
                url = f"{self.base_url}/{self.supplier_id}/products?page=0&size=100"
                response = client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", [])
                    for item in content:
                        sku = item.get("barcode") or item.get("stockCode")
                        if not sku:
                            continue
                            
                        fetched_variants.append({
                            "sku": sku,
                            "name": item.get("title", f"Trendyol Ürünü - {sku}"),
                            "price": float(item.get("salePrice", 0.0)),
                            "quantity": int(item.get("quantity", 0)),
                            "marketplace": "trendyol"
                        })
                elif response.status_code in (401, 403):
                    print("[Trendyol] Yetkilendirme hatası (API Key, Secret veya Supplier ID geçersiz)")
                else:
                    print(f"[Trendyol] API Hatası: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[Trendyol Sync Hatası]: {e}")
            
        return fetched_variants

    def fetch_orders(self) -> list:
        # TEST (MOCK) MODU
        if self.supplier_id.lower() == "test":
            from datetime import datetime
            return [
                {
                    "order_number": "TY-ORD-20001",
                    "customer_name": "Test Müşteri Trendyol",
                    "total_price": 205.50,
                    "status": "Yeni Sipariş",
                    "order_date": datetime.now().isoformat(),
                    "items": [
                        {"product_sku": "TY-TEST-001", "product_name": "Trendyol Test Ürünü 1", "quantity": 1, "price": 120.0},
                        {"product_sku": "TY-TEST-002", "product_name": "Trendyol Test Ürünü 2", "quantity": 1, "price": 85.50}
                    ]
                }
            ]
            
        fetched_orders = []
        try:
            with httpx.Client() as client:
                import datetime
                end_date = int(datetime.datetime.now().timestamp() * 1000)
                start_date = int((datetime.datetime.now() - datetime.timedelta(days=15)).timestamp() * 1000)
                
                # Trendyol Sipariş Çekme API'si
                url = f"{self.base_url}/{self.supplier_id}/orders?startDate={start_date}&endDate={end_date}&size=100"
                response = client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", [])
                    for pkg in content:
                        order_number = pkg.get("orderNumber")
                        if not order_number: continue
                        
                        customer_name = pkg.get("shipmentAddress", {}).get("fullName", "Trendyol Müşterisi")
                        
                        items = []
                        total_price = 0.0
                        
                        for line in pkg.get("lines", []):
                            price = float(line.get("price", 0.0))
                            qty = int(line.get("quantity", 1))
                            total_price += price * qty
                            
                            items.append({
                                "product_sku": line.get("barcode", "TY-UNKNOWN"),
                                "product_name": line.get("productName", ""),
                                "quantity": qty,
                                "price": price
                            })
                            
                        # Statüyü eşleştir
                        raw_status = pkg.get("status", "Created")
                        status_map = {
                            "Created": "Yeni Sipariş",
                            "Picking": "Toplanıyor",
                            "Invoiced": "Faturalandı",
                            "Shipped": "Kargolandı",
                            "Delivered": "Teslim Edildi",
                            "Cancelled": "İptal Edildi",
                            "Returned": "İade Edildi"
                        }
                        
                        # Trendyol timestamp milisaniye olarak döner
                        order_timestamp = pkg.get("orderDate", 0)
                        order_date = datetime.datetime.fromtimestamp(order_timestamp / 1000.0).isoformat() if order_timestamp else None

                        fetched_orders.append({
                            "order_number": str(order_number),
                            "customer_name": customer_name,
                            "total_price": total_price,
                            "status": status_map.get(raw_status, raw_status),
                            "order_date": order_date,
                            "items": items
                        })
                elif response.status_code in (401, 403):
                    print("[Trendyol Order] Yetkilendirme hatası")
        except Exception as e:
            print(f"[Trendyol Order Sync Hatası]: {e}")
            
        return fetched_orders

    def update_product(self, sku: str, new_price: float = None, new_stock: int = None) -> bool:
        success = True
        try:
            with httpx.Client() as client:
                url = f"{self.base_url}/{self.supplier_id}/products/price-and-inventory"
                
                payload_item = {"barcode": sku}
                if new_price is not None:
                    payload_item["salePrice"] = float(new_price)
                if new_stock is not None:
                    payload_item["quantity"] = int(new_stock)
                    
                payload = {"items": [payload_item]}
                response = client.post(url, headers=self.headers, json=payload)
                
                if response.status_code not in (200, 201, 202):
                    print(f"[Trendyol] Stok/Fiyat güncellenemedi ({sku}): {response.text}")
                    success = False
        except Exception as e:
            print(f"[Trendyol] API Hatası: {e}")
            success = False
            
        return success

    def get_product_details(self, sku: str) -> dict:
        return {"sku": sku, "name": "Trendyol Ürünü", "price": 0.0}

from sp_api.api import Orders, CatalogItems
from sp_api.base import SellingApiException
import datetime


class PazaramaAdapter(MarketplaceAdapter):
    def __init__(self, merchant_id: str, api_key: str, api_secret: str = None):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.token = None

    def _get_token(self):
        import httpx
        import base64
        if not self.api_key or not self.api_secret:
            raise Exception("Pazarama API Key (Client ID) veya Secret eksik!")
        
        auth_str = f"{self.api_key}:{self.api_secret}"
        b64_auth = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "merchantgatewayapi.fullaccess"
        }
        
        resp = httpx.post("https://isortagimgiris.pazarama.com/connect/token", headers=headers, data=data, timeout=30.0)
        if resp.status_code == 200:
            resp_json = resp.json()
            # Pazarama API standart OAuth2 yerine kendi wrapper'ını kullanıyor: {"data": {"accessToken": "..."}}
            data_obj = resp_json.get("data", {})
            if isinstance(data_obj, dict):
                self.token = data_obj.get("accessToken") or data_obj.get("access_token")
            
            # Fallback for standard OAuth2
            if not self.token:
                self.token = resp_json.get("access_token") or resp_json.get("accessToken")
                
            if not self.token:
                raise Exception(f"Pazarama token alınamadı (Yanıt 200 ama token yok): {resp.text[:300]}")
        else:
            raise Exception(f"Pazarama token alınamadı. HTTP {resp.status_code}: {resp.text[:300]}")

    async def get_categories(self):
        import httpx
        if not self.token:
            self._get_token()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        async with httpx.AsyncClient() as client:
            try:
                # Doğru endpoint: /Category/getCategoryTree
                for ep in ["/Category/getCategoryTree", "/category/category-tree", "/Category/GetCategories", "/category", "/Category"]:
                    resp = await client.get(f"https://isortagimapi.pazarama.com{ep}", headers=headers, timeout=15.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        # Eğer {"data": [...]} formatındaysa
                        if isinstance(data, dict) and "data" in data:
                            return {"isSuccess": True, "data": data["data"]}
                        return {"isSuccess": True, "data": data}
                return {"isSuccess": False, "message": "Kategori endpointi bulunamadı (404)"}
            except Exception as e:
                return {"isSuccess": False, "message": f"Kategoriler çekilirken hata: {str(e)}"}

    async def get_brands(self):
        import httpx
        if not self.token:
            self._get_token()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        async with httpx.AsyncClient() as client:
            try:
                for ep in ["/Brand/getAll", "/brand/getAll", "/Brand/GetBrands", "/brand", "/Brand"]:
                    resp = await client.get(f"https://isortagimapi.pazarama.com{ep}", headers=headers, timeout=15.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict) and "data" in data:
                            return {"isSuccess": True, "data": data["data"]}
                        return {"isSuccess": True, "data": data}
                return {"isSuccess": False, "message": "Marka endpointi bulunamadı (404)"}
            except Exception as e:
                return {"isSuccess": False, "message": f"Markalar çekilirken hata: {str(e)}"}

    def fetch_all_products(self) -> list:
        print('[Pazarama] Ürünler gerçek API\'den çekiliyor...')
        if not self.token:
            self._get_token()
            
        import httpx
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        
        all_products = []
        page = 1
        has_more = True
        
        while has_more:
            # Hem Cursor hem Page parametrelerini destekleyecek genel bir endpoint yapısı deneyelim
            # Pazarama dökümanlarında bazen /approved bazen query param olarak geçiyor.
            url = f"https://isortagimapi.pazarama.com/product/products?Approved=True&Size=100&Page={page}"
                
            resp = httpx.get(url, headers=headers, timeout=30.0)
            if resp.status_code != 200:
                alt_url = f"https://isortagimapi.pazarama.com/product/products/approved?Size=100&Page={page}"
                resp = httpx.get(alt_url, headers=headers, timeout=30.0)
                if resp.status_code != 200:
                    raise Exception(f"Pazarama API Hatası (HTTP {resp.status_code}): {resp.text[:200]}")
                
            data = resp.json()
            
            # Pazarama API bazen 'items' bazen 'products' bazen 'data' dönebilir
            items = data.get("items") or data.get("products") or data.get("data")
            
            if items is None or len(items) == 0:
                if page == 1:
                    # İlk sayfada boş dönerse direkt hata fırlat ki kullanıcı bilsin
                    raise Exception(f"Pazarama'dan boş veri döndü! Gelen ham veri: {str(data)[:200]}")
                break
                
            for item in items:
                # Fiyat ve stok alanları farklı dökümanlarda farklı olabiliyor (salePrice, listPrice, stock, stockCount)
                price = item.get("salePrice") or item.get("listPrice") or item.get("price") or 0.0
                stock = item.get("stockCount") or item.get("stock") or item.get("quantity") or 0
                all_products.append({
                    'sku': str(item.get("code") or item.get("Code") or item.get("barcode") or item.get("id") or ""),
                    'name': item.get("name") or item.get("Name") or item.get("DisplayName") or "İsimsiz Ürün",
                    'price': float(price),
                    'stock': int(stock),
                    'category_id': str(item.get("categoryId") or item.get("CategoryId") or ""),
                    'brand_id': str(item.get("brandId") or item.get("BrandId") or ""),
                    'images': item.get("images") or item.get("Images") or []
                })
                
            total_count = data.get("totalCount") or 0
            # Eğer nextCursor dönüyorsa cursor tabanlıdır, aksi halde page tabanlı
            if data.get("nextCursor"):
                # Eğer ilk dökümandaki gibi cursor tabanlıysa
                has_more = False # Cursor'u desteklemiyoruz şimdilik page yeterli
            else:
                if len(all_products) >= total_count:
                    has_more = False
                else:
                    page += 1
            
        return all_products

    def fetch_orders(self) -> list:
        print('[Pazarama] Siparişler çekiliyor (Simülasyon)...')
        from datetime import datetime
        return [
            {
                'order_number': f'PZ-{int(datetime.now().timestamp())}',
                'customer_name': 'Ahmet Yılmaz (Pazarama Müşterisi)',
                'total_price': 348.90,
                'status': 'Yeni',
                'order_date': datetime.now().isoformat(),
                'items': [
                    {'product_sku': 'PZR-001', 'product_name': 'Pazarama Test Ürünü 1', 'quantity': 1, 'price': 199.90},
                    {'product_sku': 'PZR-002', 'product_name': 'Pazarama Özel Kampanyalı Ürün', 'quantity': 1, 'price': 149.00}
                ]
            }
        ]

    def get_product_details(self, sku: str) -> dict:
        return {}

    def update_product(self, sku: str, new_price: float = None, new_stock: int = None) -> bool:
        print(f"[Pazarama] Ürün güncelleniyor: {sku}")
        if not self.token:
            self._get_token()
            
        import httpx
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        success = True
        
        # Sadece Stok Güncellemesi
        if new_stock is not None:
            stock_payload = [
                {
                    "Code": sku,
                    "StockCount": int(new_stock)
                }
            ]
            try:
                resp = httpx.post("https://isortagimapi.pazarama.com/product/updateStock", json=stock_payload, headers=headers, timeout=15.0)
                print(f"[Pazarama UpdateStock] {resp.status_code} - {resp.text[:200]}")
                if resp.status_code not in [200, 201, 202]:
                    success = False
            except Exception as e:
                print(f"[Pazarama UpdateStock Error] {e}")
                success = False
                
        # Sadece Fiyat Güncellemesi
        if new_price is not None:
            price_payload = [
                {
                    "Code": sku,
                    "ListPrice": float(new_price),
                    "SalePrice": float(new_price)
                }
            ]
            try:
                resp = httpx.post("https://isortagimapi.pazarama.com/product/updatePrice", json=price_payload, headers=headers, timeout=15.0)
                print(f"[Pazarama UpdatePrice] {resp.status_code} - {resp.text[:200]}")
                if resp.status_code not in [200, 201, 202]:
                    success = False
            except Exception as e:
                print(f"[Pazarama UpdatePrice Error] {e}")
                success = False

        return success

    def create_product(self, product_data: dict, target_category_id: str, target_brand_id: str, vat_rate: int) -> dict:
        if not self.token:
            self._get_token()
            
        import httpx
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Pazarama'nın beklediği images formatı
        pazarama_images = []
        for img in product_data.get("images", []):
            if isinstance(img, dict):
                img_url = img.get("url") or img.get("imageurl") or img.get("imageUrl")
                if img_url:
                    pazarama_images.append({"imageurl": img_url})
            elif isinstance(img, str):
                pazarama_images.append({"imageurl": img})
        
        if not pazarama_images:
            pazarama_images.append({"imageurl": "https://via.placeholder.com/500"})
        payload = {
            "products": [
                {
                    "Name": product_data.get("name")[:100],
                    "DisplayName": product_data.get("name")[:100],
                    "Description": product_data.get("description", "Açıklama bulunmuyor.") or "Açıklama bulunmuyor.",
                    "BrandId": str(target_brand_id),
                    "CategoryId": str(target_category_id),
                    "Code": str(product_data.get("sku")),
                    "GroupCode": str(product_data.get("sku")),
                    "StockCount": int(product_data.get("stock", 0)),
                    "VatRate": int(vat_rate),
                    "ListPrice": float(product_data.get("price", 0.0)),
                    "SalePrice": float(product_data.get("price", 0.0)),
                    "Desi": 1,
                    "images": pazarama_images
                }
            ]
        }
        
        try:
            import time
            max_retries = 3
            for attempt in range(max_retries):
                resp = httpx.post("https://isortagimapi.pazarama.com/product/create", headers=headers, json=payload, timeout=30.0)
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(1.5)
                        continue
                
                if resp.status_code not in (200, 201):
                    raise Exception(f"Pazarama Ürün Oluşturma Hatası (HTTP {resp.status_code}): {resp.text[:300]}")
                    
                resp_data = resp.json()
                return {"success": True, "message": "Ürün başarıyla Pazarama'ya aktarıldı ve onay sürecine girdi.", "data": resp_data}
        except Exception as e:
            raise Exception(f"Pazarama'ya ürün aktarılırken hata oluştu: {str(e)}")

    def create_products_bulk(self, products_payload: list) -> dict:
        if not self.token:
            self._get_token()
            
        import httpx
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "products": products_payload
        }
        
        try:
            import time
            max_retries = 3
            for attempt in range(max_retries):
                resp = httpx.post("https://isortagimapi.pazarama.com/product/create", headers=headers, json=payload, timeout=60.0)
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(3.0)
                        continue
                
                if resp.status_code not in (200, 201):
                    raise Exception(f"Pazarama Toplu Ürün Oluşturma Hatası (HTTP {resp.status_code}): {resp.text[:500]}")
                    
                resp_data = resp.json()
                return {"success": True, "message": f"{len(products_payload)} adet ürün başarıyla aktarıldı.", "data": resp_data}
        except Exception as e:
            raise Exception(f"Pazarama'ya toplu ürün aktarılırken hata oluştu: {str(e)}")

class AmazonAdapter(MarketplaceAdapter):
    def __init__(self, seller_id: str, refresh_token: str, region: str = "EU", lwa_client_id: str = None, lwa_client_secret: str = None):
        self.seller_id = seller_id
        self.refresh_token = refresh_token
        
        # Region ayırma mantığı
        if "|" in self.seller_id:
            parts = self.seller_id.split("|")
            self.region = parts[0]
            self.seller_id = parts[1]
        else:
            self.region = region
            
        self.lwa_client_id = lwa_client_id
        self.lwa_client_secret = lwa_client_secret
        self._access_token = None
        
        # Region mapping
        regions = {
            "EU": "https://sellingpartnerapi-eu.amazon.com",
            "NA": "https://sellingpartnerapi-na.amazon.com",
            "FE": "https://sellingpartnerapi-fe.amazon.com"
        }
        self.base_url = regions.get(self.region, "https://sellingpartnerapi-eu.amazon.com")
        self.marketplace_id = "A33AVAJ2PDY396" # TR Marketplace ID (Şimdilik varsayılan TR)

    def _get_token(self):
        if self._access_token:
            return self._access_token
            
        import httpx
        url = "https://api.amazon.com/auth/o2/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.lwa_client_id,
            "client_secret": self.lwa_client_secret
        }
        resp = httpx.post(url, data=payload, timeout=15.0)
        if resp.status_code != 200:
            raise Exception(f"Amazon yetkilendirme hatası: {resp.text}")
            
        self._access_token = resp.json().get("access_token")
        return self._access_token

    def fetch_all_products(self) -> list:
        # Gerçek senaryoda Reports API ile GET_MERCHANT_LISTINGS_ALL_DATA raporu oluşturulup asenkron beklenir.
        # Basitlik ve hız adına şimdilik boş dönüyoruz veya sadece elimizdeki SKU'yu get_product_details ile çekeriz.
        # Test amaçlı manuel olarak hata fırlatmıyoruz, boş liste dönüyoruz.
        print('[Amazon] Ürünler çekiliyor... (Rapor API entegrasyonu gerektirir)')
        return []

    def fetch_orders(self) -> list:
        import httpx
        from datetime import datetime, timedelta
        
        token = self._get_token()
        headers = {
            "x-amz-access-token": token,
            "Content-Type": "application/json"
        }
        
        created_after = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
        url = f"{self.base_url}/orders/v0/orders?MarketplaceIds={self.marketplace_id}&CreatedAfter={created_after}"
        
        try:
            resp = httpx.get(url, headers=headers, timeout=20.0)
            if resp.status_code != 200:
                print(f"[Amazon] Sipariş çekme hatası: {resp.text}")
                return []
                
            orders_data = resp.json().get("payload", {}).get("Orders", [])
            results = []
            
            for o in orders_data:
                # Sipariş detaylarını almak için
                order_id = o.get("AmazonOrderId")
                items_url = f"{self.base_url}/orders/v0/orders/{order_id}/orderItems"
                items_resp = httpx.get(items_url, headers=headers, timeout=15.0)
                
                order_items = []
                if items_resp.status_code == 200:
                    for i in items_resp.json().get("payload", {}).get("OrderItems", []):
                        order_items.append({
                            "product_sku": i.get("SellerSKU", "AMZ-UNKNOWN"),
                            "product_name": i.get("Title", ""),
                            "quantity": i.get("QuantityOrdered", 1),
                            "price": float(i.get("ItemPrice", {}).get("Amount", 0.0))
                        })
                
                results.append({
                    "order_number": order_id,
                    "customer_name": o.get("BuyerInfo", {}).get("BuyerName", "Amazon Müşterisi"),
                    "total_price": float(o.get("OrderTotal", {}).get("Amount", 0.0)) if o.get("OrderTotal") else 0.0,
                    "status": o.get("OrderStatus", "Pending"),
                    "order_date": o.get("PurchaseDate"),
                    "items": order_items
                })
                
            return results
        except Exception as e:
            print(f"[Amazon] Hata (fetch_orders): {e}")
            return []

    def update_product(self, sku: str, new_price: float = None, new_stock: int = None) -> bool:
        try:
            import httpx
            token = self._get_token()
            headers = {
                "x-amz-access-token": token,
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/listings/2021-08-01/items/{self.seller_id}/{sku}?marketplaceIds={self.marketplace_id}"
            
            patches = []
            if new_price is not None:
                patches.append({
                    "op": "replace",
                    "path": "/purchasable_offer/1/our_price",
                    "value": [
                        {
                            "marketplace_id": self.marketplace_id,
                            "currency": "TRY",
                            "amount": float(new_price)
                        }
                    ]
                })
            if new_stock is not None:
                patches.append({
                    "op": "replace",
                    "path": "/fulfillment_availability/1/quantity",
                    "value": [
                        {
                            "fulfillment_channel_code": "DEFAULT",
                            "quantity": int(new_stock)
                        }
                    ]
                })
            
            if not patches:
                return True
                
            payload = {
                "productType": "PRODUCT",
                "patches": patches
            }
            
            resp = httpx.patch(url, headers=headers, json=payload, timeout=15.0)
            print(f"[Amazon] PATCH sonucu ({sku}): {resp.status_code} - {resp.text}")
            
            if resp.status_code in (200, 201, 202, 204):
                return True
            return False
        except Exception as e:
            print(f"[Amazon] Fiyat/Stok güncelleme hatası ({sku}): {e}")
            return False
        
    def get_product_details(self, sku: str) -> dict:
        return {}

    def create_products_bulk(self, products_payload: list) -> dict:
        """
        Amazon Listings API v2021-08-01 kullanarak toplu ürün yükler.
        Amazon API'si aslında tek tek (PUT) veya Feed tabanlı (Batch) kabul eder.
        Basitlik adına burada ürünleri bir döngüde asenkron olarak yolluyoruz.
        """
        import httpx
        import asyncio
        
        try:
            token = self._get_token()
        except Exception as e:
            return {"success": False, "message": f"Amazon Token alınamadı: {str(e)}"}
            
        headers = {
            "x-amz-access-token": token,
            "Content-Type": "application/json"
        }
        
        results = []
        success_count = 0
        error_messages = []
        
        for p in products_payload:
            sku = p.get("sku")
            if not sku:
                continue
                
            # Amazon SP-API Listings Items Payload (PRODUCT type - v2021-08-01)
            # Not: Gerçekte her kategoriye özel detaylı attributes gerekir.
            # Şimdilik en basit versiyonu yolluyoruz.
            url = f"{self.base_url}/listings/2021-08-01/items/{self.seller_id}/{sku}?marketplaceIds={self.marketplace_id}"
            
            payload = {
                "productType": "PRODUCT",
                "requirements": "LISTING",
                "attributes": {
                    "item_name": [{"value": p.get("name", "")[:200], "language_tag": "tr_TR"}],
                    "purchasable_offer": [{
                        "currency": p.get("currency", "TRY"),
                        "our_price": [{"schedule": [{"value_with_tax": float(p.get("price", 0.0))}]}]
                    }],
                    "fulfillment_availability": [{
                        "fulfillment_channel_code": "DEFAULT",
                        "quantity": int(p.get("stock", 0))
                    }],
                    "merchant_suggested_asin": [{"value": sku}] # Test amaçlı, genelde barcode gerekir
                }
            }
            
            try:
                # Amazon'da yeni ürün oluşturmak PUT isteği ile yapılır
                resp = httpx.put(url, headers=headers, json=payload, timeout=20.0)
                
                # Rate limit koruması
                if resp.status_code == 429:
                    import time
                    time.sleep(2)
                    resp = httpx.put(url, headers=headers, json=payload, timeout=20.0)
                    
                if resp.status_code in (200, 201, 202):
                    success_count += 1
                    results.append({"sku": sku, "status": "success"})
                else:
                    results.append({"sku": sku, "status": "error", "reason": resp.text})
                    error_messages.append(f"{sku}: {resp.text[:200]}")
            except Exception as e:
                results.append({"sku": sku, "status": "error", "reason": str(e)})
                error_messages.append(f"{sku}: {str(e)}")
                
        if success_count == len(products_payload) and len(products_payload) > 0:
            return {"success": True, "message": f"{success_count} ürün Amazon'a başarıyla aktarıldı.", "results": results}
        elif success_count > 0:
            return {"success": True, "message": f"{success_count} ürün aktarıldı, {len(products_payload) - success_count} ürün hatalı.", "results": results, "errors": error_messages}
        else:
            return {"success": False, "message": "Hiçbir ürün aktarılamadı.", "results": results, "errors": error_messages}

