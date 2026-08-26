import asyncio
import httpx
from core.database import AsyncSessionLocal
from models.integration import MarketplaceIntegration
from sqlalchemy import select
from services.marketplace import PazaramaAdapter

async def test():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MarketplaceIntegration).filter_by(marketplace_name="pazarama"))
        integration = result.scalars().first()
        if not integration:
            print("No integration found")
            return
            
        adapter = PazaramaAdapter(integration)
        token = await adapter._get_token()
        
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            print("Testing /Category...")
            cat_res = await client.get("https://isortagimapi.pazarama.com/Category", headers=headers)
            print("Category Status:", cat_res.status_code)
            if cat_res.status_code == 200:
                print("Category Data:", str(cat_res.json())[:500])
                
            print("\nTesting /Brand...")
            brand_res = await client.get("https://isortagimapi.pazarama.com/Brand", headers=headers)
            print("Brand Status:", brand_res.status_code)
            if brand_res.status_code == 200:
                print("Brand Data:", str(brand_res.json())[:500])

if __name__ == "__main__":
    asyncio.run(test())
