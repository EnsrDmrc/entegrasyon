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
                response = client.get(f"{self.base_url}/products.json", headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    return {"sku": sku, "name": "Shopify'dan Çekilen Ürün", "price": 100.0}
        except Exception as e:
            print(f"[Shopify] API Hatası: {e}")
        return {"sku": sku, "name": "Bilinmeyen Ürün", "price": 0.0}

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
