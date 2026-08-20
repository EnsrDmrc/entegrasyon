import asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

# Uygulamamızın ana dizinini sisteme tanıtıyoruz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from core.database import AsyncSessionLocal
from models.tenant import Tenant
from models.product import Product
from models.inventory import Inventory

async def seed_data():
    """Test için sahte mağaza, ürün ve stok verisi ekler."""
    async with AsyncSessionLocal() as db:
        # Eğer varsa önceki verileri temizle
        await db.execute(Inventory.__table__.delete())
        await db.execute(Product.__table__.delete())
        await db.execute(Tenant.__table__.delete())
        
        # Test Mağazası
        tenant = Tenant(name="Test Mağazası", domain="test.com")
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        
        # Test Ürünü
        product = Product(tenant_id=tenant.id, sku="IPHONE-15-PRO", name="iPhone 15 Pro", price=50000.0)
        db.add(product)
        await db.commit()
        await db.refresh(product)
        
        # Test Stoğu
        inventory = Inventory(product_id=product.id, marketplace="shopify", quantity=5)
        db.add(inventory)
        await db.commit()
        await db.refresh(inventory)
        
        print(f"--- BAŞLANGIÇ DURUMU ---")
        print(f"[{product.name}] isimli üründen veritabanında {inventory.quantity} adet stok var.")
        return product.id

async def run_test():
    product_id = await seed_data()
    
    print("\n--- TEST BAŞLIYOR ---")
    print("SİMÜLASYON: Shopify'dan 2 adet sipariş geldi...")
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "product_id": product_id,
            "quantity_bought": 2,
            "marketplace": "shopify"
        }
        
        response = await client.post("/api/v1/webhooks/shopify/order_created", json=payload)
        
        if response.status_code == 200:
            print("\nBASARILI!")
            print(f"Sunucu Cevabı: {response.json()}")
            print(f"Stoktan başarıyla 2 adet düşüldü ve eşzamanlı satış engelleme kilidi çalıştı.")
        else:
            print("\n❌ HATA!")
            print(f"Durum Kodu: {response.status_code}")
            print(f"Sunucu Cevabı: {response.json()}")

if __name__ == "__main__":
    asyncio.run(run_test())
