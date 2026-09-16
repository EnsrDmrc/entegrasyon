import asyncio
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.integration import MarketplaceIntegration
from services.marketplace import PazaramaAdapter

async def test_stock():
    async with AsyncSessionLocal() as db:
        ints_res = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "pazarama", MarketplaceIntegration.is_active == True))
        ints = ints_res.scalars().all()
        
        if not ints:
            print("No active Pazarama integration found.")
            return
            
        integration = ints[0]
        adapter = PazaramaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret) if integration.api_secret else None)
        
        sku = "yld14x15.."
        new_stock = 99
        
        print(f"Testing stock update for SKU: {sku} with stock: {new_stock}")
        result = adapter.update_product(sku=sku, new_stock=new_stock)
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_stock())
