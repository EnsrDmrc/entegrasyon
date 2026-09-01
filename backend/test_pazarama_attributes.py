import asyncio
import httpx
from core.database import AsyncSessionLocal
from models.integration import MarketplaceIntegration
from sqlalchemy.future import select
from services.marketplace import PazaramaAdapter

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MarketplaceIntegration).filter(MarketplaceIntegration.marketplace_name.ilike("%pazarama%")))
        integration = result.scalars().first()
        
    if not integration:
        print("Pazarama entegrasyonu bulunamadı.")
        return

    adapter = PazaramaAdapter(
        merchant_id=str(integration.store_url),
        api_key=str(integration.api_key),
        api_secret=str(integration.api_secret)
    )
    if not adapter.token:
        adapter._get_token()
        
    headers = {
        "Authorization": f"Bearer {adapter.token}",
        "Accept": "application/json"
    }
    
    # Let's get the categories first to pick a random leaf category
    cats_resp = await adapter.get_categories()
    categories = cats_resp.get("data", []) if isinstance(cats_resp, dict) else cats_resp
    
    if not categories:
        print("Kategori bulunamadı.")
        return
        
    # Find a leaf category (one without children or just pick the first one)
    target_cat = categories[-1]
    cat_id = target_cat.get("id") or target_cat.get("Id")
    cat_name = target_cat.get("name") or target_cat.get("Name")
    
    print(f"Testing Category: {cat_name} (ID: {cat_id})")
    
    # Fetch attributes
    url = f"https://isortagimapi.pazarama.com/Category/{cat_id}/Attributes"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            attrs = resp.json()
            print("Attributes:", attrs)
        else:
            print("Error fetching attributes:", resp.status_code, resp.text)

if __name__ == "__main__":
    asyncio.run(main())
