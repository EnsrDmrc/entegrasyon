import ast

def clean_file():
    with open('services/marketplace.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    keep_lines = lines[:768]
    
    pazarama_code = '''
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
            self.token = resp.json().get("access_token")
        else:
            raise Exception(f"Pazarama token alınamadı. HTTP {resp.status_code}: {resp.text}")

    def fetch_all_products(self) -> list:
        print('[Pazarama] Ürünler gerçek API\\'den çekiliyor...')
        if not self.token:
            self._get_token()
            
        import httpx
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        
        all_products = []
        next_cursor = None
        has_more = True
        
        while has_more:
            url = "https://isortagimapi.pazarama.com/product/products/approved?Size=100"
            if next_cursor:
                url += f"&Cursor={next_cursor}"
                
            resp = httpx.get(url, headers=headers, timeout=30.0)
            if resp.status_code != 200:
                print(f"[Pazarama Error] Ürünler çekilemedi. HTTP {resp.status_code}: {resp.text}")
                break
                
            data = resp.json()
            items = data.get("items", [])
            for item in items:
                all_products.append({
                    'sku': item.get("code", ""),
                    'name': item.get("name", "İsimsiz Ürün"),
                    'price': float(item.get("salePrice", 0.0) or 0.0),
                    'stock': int(item.get("stockCount", 0) or 0)
                })
                
            next_cursor = data.get("nextCursor")
            has_more = bool(next_cursor)
            
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

    def update_product(self, sku: str, new_price: float = None, new_stock: int = None) -> bool:
        print(f"[Pazarama] Ürün güncelleniyor: {sku}")
        return True
        
    def get_product_details(self, sku: str) -> dict:
        print(f"[Pazarama] Ürün detayı getiriliyor: {sku}")
        return {}

class AmazonAdapter(MarketplaceAdapter):
    def __init__(self, seller_id: str, refresh_token: str, region: str = "EU", lwa_client_id: str = None, lwa_client_secret: str = None):
        self.seller_id = seller_id
        self.refresh_token = refresh_token
        self.region = region
        self.lwa_client_id = lwa_client_id
        self.lwa_client_secret = lwa_client_secret

    def fetch_all_products(self) -> list:
        print('[Amazon] Ürünler çekiliyor (Simülasyon)...')
        return [
            {'sku': 'AMZ-001', 'name': 'Amazon Test Ürünü 1', 'price': 299.90, 'stock': 100},
            {'sku': 'AMZ-002', 'name': 'Amazon Kampanyalı Ürün', 'price': 249.00, 'stock': 50}
        ]

    def fetch_orders(self) -> list:
        print('[Amazon] Siparişler çekiliyor (Simülasyon)...')
        from datetime import datetime
        return [
            {
                'order_number': f'AMZ-{int(datetime.now().timestamp())}',
                'customer_name': 'Ayşe Kaya (Amazon Müşterisi)',
                'total_price': 548.90,
                'status': 'Yeni',
                'order_date': datetime.now().isoformat(),
                'items': [
                    {'product_sku': 'AMZ-001', 'product_name': 'Amazon Test Ürünü 1', 'quantity': 1, 'price': 299.90},
                    {'product_sku': 'AMZ-002', 'product_name': 'Amazon Kampanyalı Ürün', 'quantity': 1, 'price': 249.00}
                ]
            }
        ]

    def update_product(self, sku: str, new_price: float = None, new_stock: int = None) -> bool:
        print(f"[Amazon] Ürün güncelleniyor: {sku}")
        return True
        
    def get_product_details(self, sku: str) -> dict:
        print(f"[Amazon] Ürün detayı getiriliyor: {sku}")
        return {}
'''
    with open('services/marketplace.py', 'w', encoding='utf-8') as f:
        f.writelines(keep_lines)
        f.write(pazarama_code)

clean_file()
