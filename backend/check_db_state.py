import asyncio
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.product import Product
from models.integration import MarketplaceIntegration

async def check_db():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Product).where(Product.n11_url != None))
        prods = res.scalars().all()
        print(f"Products with n11_url: {len(prods)}")
        for p in prods:
            print(f"ID: {p.id}, SKU: {p.sku}, URL: {p.n11_url}")
            
        res2 = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "n11", MarketplaceIntegration.is_active == True))
        ints = res2.scalars().all()
        print(f"Active N11 Integrations: {len(ints)}")
        for i in ints:
            print(f"ID: {i.id}, Tenant ID: {i.tenant_id}, API Key: {i.api_key}")

if __name__ == "__main__":
    asyncio.run(check_db())
