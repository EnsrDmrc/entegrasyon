import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from core.config import settings
from models.integration import MarketplaceIntegration
import httpx

async def debug_shopify():
    engine = create_async_engine(settings.ASYNC_DATABASE_URI)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as db:
        result = await db.execute(
            select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "shopify")
        )
        integration = result.scalars().first()
        
        if not integration:
            print("No Shopify integration found.")
            return

        base_url = f"https://{integration.store_url}/admin/api/2024-01"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": integration.api_key
        }

        url = f"{base_url}/products.json?limit=250"
        page = 1
        total_products = 0
        total_variants_with_sku = 0
        
        print(f"Starting fetch for {integration.store_url}...")
        with httpx.Client() as client:
            while url:
                print(f"Fetching page {page}: {url}")
                response = client.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"Error {response.status_code}: {response.text}")
                    break
                
                data = response.json()
                products = data.get("products", [])
                print(f"Page {page} returned {len(products)} products.")
                total_products += len(products)
                
                for prod in products:
                    for var in prod.get("variants", []):
                        if var.get("sku"):
                            total_variants_with_sku += 1
                
                if "next" in response.links:
                    url = str(response.links["next"]["url"])
                    page += 1
                else:
                    print("No more pages.")
                    url = None
                    
        print(f"Total products fetched: {total_products}")
        print(f"Total variants with SKU: {total_variants_with_sku}")

if __name__ == "__main__":
    asyncio.run(debug_shopify())
