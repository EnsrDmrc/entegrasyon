import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from core.config import settings
from models.integration import MarketplaceIntegration
from services.marketplace import N11Adapter

async def main():
    engine = create_async_engine(settings.ASYNC_DATABASE_URI)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        result = await db.execute(
            select(MarketplaceIntegration)
            .where(MarketplaceIntegration.marketplace_name == "n11", MarketplaceIntegration.is_active == True)
        )
        integration = result.scalars().first()
        
    if not integration:
        print("N11 entegrasyonu bulunamadı.")
        return
        
    adapter = N11Adapter(api_key=str(integration.api_key), api_secret=str(integration.api_secret))
    products = adapter.fetch_all_products()
    if not products:
        print("Ürün bulunamadı")
        return
        
    sku = products[0]["sku"]
    print(f"Fetching details for SKU: {sku}")
    
    try:
        res = adapter.product_client.service.GetProductBySellerCode(auth=adapter.auth, sellerCode=sku)
        prod = res.product
        
        print("\n--- Kategori Bilgisi ---")
        if hasattr(prod, 'category') and prod.category:
            print("Category keys/attrs:", dir(prod.category))
            print("Category:", prod.category)
            
        print("\n--- Özellik (Attribute) Bilgisi ---")
        if hasattr(prod, 'attributes') and prod.attributes:
            print("Attributes keys/attrs:", dir(prod.attributes))
            if hasattr(prod.attributes, 'attribute'):
                for attr in prod.attributes.attribute:
                    print("Attr:", attr.name, "=>", attr.value)
    except Exception as e:
        print("Hata:", e)

if __name__ == "__main__":
    asyncio.run(main())
