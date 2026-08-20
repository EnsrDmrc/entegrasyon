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


import xml.etree.ElementTree as ET

class N11Adapter(MarketplaceAdapter):
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        
    def _get_auth_xml(self) -> str:
        return f"""
         <auth>
            <appKey>{self.api_key}</appKey>
            <appSecret>{self.api_secret}</appSecret>
         </auth>
        """

    def fetch_all_products(self) -> list:
        fetched_variants = []
        try:
            with httpx.Client() as client:
                current_page = 0
                page_size = 100
                total_pages = 1
                
                while current_page <= total_pages:
                    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
                    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sch="http://www.n11.com/ws/schemas">
                       <soapenv:Header/>
                       <soapenv:Body>
                          <sch:GetProductListRequest>
                             {self._get_auth_xml()}
                             <pagingData>
                                <currentPage>{current_page}</currentPage>
                                <pageSize>{page_size}</pageSize>
                             </pagingData>
                          </sch:GetProductListRequest>
                       </soapenv:Body>
                    </soapenv:Envelope>"""
                    
                    headers = {"Content-Type": "text/xml; charset=utf-8"}
                    res = client.post("https://api.n11.com/ws/ProductService.wsdl", content=payload, headers=headers)
                    if res.status_code != 200:
                        fault = ""
                        try:
                            fault_root = ET.fromstring(res.text)
                            fault_elem = fault_root.find(".//faultstring")
                            if fault_elem is not None:
                                fault = fault_elem.text
                        except:
                            pass
                        raise Exception(f"N11 API Hatası: {fault or res.text}")
                        
                    root = ET.fromstring(res.text)
                    namespaces = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/', 'n11': 'http://www.n11.com/ws/schemas'}
                    
                    # Check for internal N11 failure despite HTTP 200
                    status_elem = root.find(".//result/status", namespaces)
                    if status_elem is not None and status_elem.text == "failure":
                        err_msg = root.find(".//result/errorMessage", namespaces)
                        err_text = err_msg.text if err_msg is not None else "Bilinmeyen N11 hatası."
                        raise Exception(f"N11 API Hatası: {err_text}")
                    
                    # Extract total pages on first request
                    if current_page == 0:
                        page_count_elem = root.find(".//n11:pageCount", namespaces)
                        if page_count_elem is not None and page_count_elem.text:
                            total_pages = int(page_count_elem.text)
                    
                    products = root.findall(".//n11:product", namespaces)
                    if not products:
                        break
                        
                    for prod in products:
                        sku_elem = prod.find("n11:productSellerCode", namespaces)
                        title_elem = prod.find("n11:title", namespaces)
                        price_elem = prod.find("n11:price", namespaces)
                        
                        # Note: GetProductList doesn't always return exact stock details. 
                        # We might need to use GetProductBySellerCode for deep details, 
                        # but for now we try to get stock if it exists or default to 0.
                        sku = sku_elem.text if sku_elem is not None else ""
                        if not sku:
                            continue
                            
                        title = title_elem.text if title_elem is not None else ""
                        price = float(price_elem.text) if price_elem is not None else 0.0
                        
                        # We will just fetch deep details to get accurate stock since N11 list response often omits it
                        # For prototyping, we set stock to 1 if not easily parseable
                        fetched_variants.append({
                            "sku": sku,
                            "name": title,
                            "price": price,
                            "quantity": 1,  # Deep stock fetch usually requires GetProductBySellerCode loop
                            "marketplace": "n11"
                        })
                    
                    current_page += 1

        except Exception as e:
            print(f"[n11 Sync Hatası]: {e}")
            raise e
            
        return fetched_variants

    def fetch_orders(self) -> list:
        fetched_orders = []
        try:
            with httpx.Client() as client:
                payload = f"""<?xml version="1.0" encoding="UTF-8"?>
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sch="http://www.n11.com/ws/schemas">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <sch:OrderListRequest>
                         {self._get_auth_xml()}
                         <searchData>
                            <status>New</status>
                         </searchData>
                         <pagingData>
                            <currentPage>0</currentPage>
                            <pageSize>100</pageSize>
                         </pagingData>
                      </sch:OrderListRequest>
                   </soapenv:Body>
                </soapenv:Envelope>"""
                
                headers = {"Content-Type": "text/xml; charset=utf-8"}
                res = client.post("https://api.n11.com/ws/OrderService.wsdl", content=payload, headers=headers)
                if res.status_code != 200:
                    fault = ""
                    try:
                        fault_root = ET.fromstring(res.text)
                        fault_elem = fault_root.find(".//faultstring")
                        if fault_elem is not None:
                            fault = fault_elem.text
                    except:
                        pass
                    raise Exception(f"N11 API Hatası: {fault or res.text}")

                if res.status_code == 200:
                    root = ET.fromstring(res.text)
                    namespaces = {'n11': 'http://www.n11.com/ws/schemas'}
                    
                    # Check for internal N11 failure
                    status_elem = root.find(".//result/status", namespaces)
                    if status_elem is not None and status_elem.text == "failure":
                        err_msg = root.find(".//result/errorMessage", namespaces)
                        err_text = err_msg.text if err_msg is not None else "Bilinmeyen N11 hatası."
                        raise Exception(f"N11 API Hatası: {err_text}")
                    
                    orders = root.findall(".//n11:order", namespaces)
                    for ord_elem in orders:
                        order_id = ord_elem.find("n11:id", namespaces)
                        order_num = ord_elem.find("n11:orderNumber", namespaces)
                        buyer = ord_elem.find(".//n11:buyer/n11:fullName", namespaces)
                        status = ord_elem.find("n11:status", namespaces)
                        date = ord_elem.find("n11:createDate", namespaces)
                        
                        items = []
                        # N11 order items are in itemList
                        item_list = ord_elem.findall(".//n11:itemList/n11:item", namespaces)
                        total_price = 0.0
                        for item in item_list:
                            sku = item.find("n11:productSellerCode", namespaces)
                            title = item.find("n11:productName", namespaces)
                            qty = item.find("n11:quantity", namespaces)
                            price = item.find("n11:price", namespaces)
                            
                            i_qty = int(qty.text) if qty is not None else 1
                            i_price = float(price.text) if price is not None else 0.0
                            
                            total_price += i_price * i_qty
                            
                            items.append({
                                "product_sku": sku.text if sku is not None else "N11-NO-SKU",
                                "product_name": title.text if title is not None else "",
                                "quantity": i_qty,
                                "price": i_price
                            })

                        fetched_orders.append({
                            "order_number": order_num.text if order_num is not None else (order_id.text if order_id is not None else ""),
                            "customer_name": buyer.text if buyer is not None else "N11 Müşteri",
                            "total_price": total_price,
                            "status": status.text if status is not None else "New",
                            "order_date": date.text if date is not None else None,
                            "items": items
                        })
        except Exception as e:
            print(f"[n11 Order Sync Hatası]: {e}")
            raise e
            
        return fetched_orders

    def update_product(self, sku: str, new_price: float = None, new_stock: int = None) -> bool:
        # Stock Update Request
        if new_stock is not None:
            try:
                with httpx.Client() as client:
                    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
                    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sch="http://www.n11.com/ws/schemas">
                       <soapenv:Header/>
                       <soapenv:Body>
                          <sch:UpdateStockByStockSellerCodeRequest>
                             {self._get_auth_xml()}
                             <stockSellerCode>{sku}</stockSellerCode>
                             <stockItems>
                                <stockItem>
                                   <sellerStockCode>{sku}</sellerStockCode>
                                   <quantity>{new_stock}</quantity>
                                </stockItem>
                             </stockItems>
                          </sch:UpdateStockByStockSellerCodeRequest>
                       </soapenv:Body>
                    </soapenv:Envelope>"""
                    
                    headers = {"Content-Type": "text/xml; charset=utf-8"}
                    res = client.post("https://api.n11.com/ws/ProductService.wsdl", content=payload, headers=headers)
                    if res.status_code != 200:
                        return False
            except Exception:
                return False
                
        # Price Update Request
        if new_price is not None:
            try:
                with httpx.Client() as client:
                    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
                    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sch="http://www.n11.com/ws/schemas">
                       <soapenv:Header/>
                       <soapenv:Body>
                          <sch:UpdateProductPriceBySellerCodeRequest>
                             {self._get_auth_xml()}
                             <productSellerCode>{sku}</productSellerCode>
                             <price>{new_price}</price>
                             <currencyType>1</currencyType>
                          </sch:UpdateProductPriceBySellerCodeRequest>
                       </soapenv:Body>
                    </soapenv:Envelope>"""
                    headers = {"Content-Type": "text/xml; charset=utf-8"}
                    res = client.post("https://api.n11.com/ws/ProductService.wsdl", content=payload, headers=headers)
            except Exception:
                return False
                
        return True

    def get_product_details(self, sku: str) -> dict:
        return {"sku": sku, "name": "Test Product n11", "price": 100.0}

