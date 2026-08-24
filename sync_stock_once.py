import asyncio
import os
import sys

# Backend dizinini yola ekle ki modüller import edilebilsin
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from backend.models.product import Product
from backend.models.inventory import Inventory
from backend.models.integration import MarketplaceIntegration
from backend.services.marketplace import ShopifyAdapter

async def run_one_time_sync():
    print("N11 stokları Shopify'a aktarılıyor. Lütfen bekleyin...")
    
    engine = create_async_engine("postgresql+asyncpg://postgres:ensarbaba123@localhost:5432/entegrasyon_db")
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as db:
        # Tüm Shopify entegrasyonlarını bul (Tenant'lar için)
        integrations_result = await db.execute(
            select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "shopify", MarketplaceIntegration.is_active == True)
        )
        integrations = integrations_result.scalars().all()
        
        if not integrations:
            print("Aktif Shopify entegrasyonu bulunamadı!")
            return
            
        for integration in integrations:
            print(f"\nTenant ID {integration.tenant_id} için işlemler başlatılıyor...")
            
            # Bu tenant'a ait ürünleri bul
            products_result = await db.execute(
                select(Product).where(Product.tenant_id == integration.tenant_id)
            )
            products = products_result.scalars().all()
            
            shopify_adapter = ShopifyAdapter(api_key=integration.api_key, store_url=integration.store_url)
            
            success_count = 0
            for product in products:
                # Ürünün N11 stoğunu bul
                inv_result = await db.execute(
                    select(Inventory).where(Inventory.product_id == product.id, Inventory.marketplace == "n11")
                )
                n11_inv = inv_result.scalars().first()
                
                if n11_inv:
                    print(f"[{product.sku}] N11 Stoğu: {n11_inv.quantity} -> Shopify'a gönderiliyor...")
                    # Shopify'a gönder
                    try:
                        res = shopify_adapter.update_product(sku=product.sku, new_stock=n11_inv.quantity)
                        if res:
                            success_count += 1
                        else:
                            print(f"[{product.sku}] Shopify'da güncellenemedi (SKU bulunamamış olabilir).")
                    except Exception as e:
                        print(f"[{product.sku}] Hata: {e}")
            
            print(f"Tenant ID {integration.tenant_id} için {success_count} ürün Shopify'da güncellendi!")

if __name__ == "__main__":
    asyncio.run(run_one_time_sync())
