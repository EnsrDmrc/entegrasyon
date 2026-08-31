import httpx
import asyncio
from core.database import AsyncSessionLocal
from models.integration import MarketplaceIntegration
from sqlalchemy.future import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MarketplaceIntegration))
        integrations = result.scalars().all()
        for i in integrations:
            print(f"ID: {i.id}, Name: {i.marketplace_name}")
            if i.marketplace_name.lower() == "pazarama":
                integration = i
        
    if 'integration' not in locals():
        print("Pazarama entegrasyonu bulunamadı.")
        return

    # Use the token directly or fetch it. Since Pazarama uses a client_id and secret, 
    # we should use the adapter to get the token.
    from services.marketplace import PazaramaAdapter
    adapter = PazaramaAdapter(
        seller_id=integration.seller_id,
        refresh_token=integration.api_secret or integration.api_key
    )
    
    if not adapter.token:
        adapter._get_token()
        
    headers = {
        "Authorization": f"Bearer {adapter.token}",
        "Accept": "application/json"
    }
    
    batch_id = "1c1cb4eb-62da-4b2e-9426-0b8e57fb5f0f"
    endpoints = [
        f"/product/BatchRequestResult?batchRequestId={batch_id}",
        f"/product/batchRequestResult?batchRequestId={batch_id}",
        f"/Product/BatchRequestResult?batchRequestId={batch_id}",
        f"/product/getBatchRequestResult?batchRequestId={batch_id}",
        f"/product/batch-status?batchRequestId={batch_id}",
        f"/product/status?batchRequestId={batch_id}"
    ]
    
    async with httpx.AsyncClient(base_url="https://isortagimapi.pazarama.com") as client:
        for ep in endpoints:
            print(f"Testing {ep}...")
            resp = await client.get(ep, headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("Response:", resp.json())
                break
                
if __name__ == "__main__":
    asyncio.run(main())
