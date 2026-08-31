import asyncio
import httpx
import os
import sys

# To allow importing from backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from core.config import settings
from models.integration import MarketplaceIntegration

async def main():
    engine = create_async_engine(settings.ASYNC_DATABASE_URI)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        result = await db.execute(
            select(MarketplaceIntegration)
            .where(MarketplaceIntegration.marketplace_name == "pazarama")
        )
        integration = result.scalars().first()
        
    if not integration:
        print("Pazarama entegrasyonu bulunamadı.")
        return
        
    merchant_id = integration.store_url
    api_key = integration.api_key
    api_secret = integration.api_secret
    
    print(f"Merchant ID: {merchant_id}, API Key: {api_key}")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "client_id": api_key,
        "client_secret": api_secret
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "merchantgatewayapi.fullaccess"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://isortagimgiris.pazarama.com/connect/token", headers=headers, data=data)
        if resp.status_code != 200:
            print("Token alınamadı:", resp.text)
            return
            
        token_data = resp.json()
        token = token_data.get("data", {}).get("accessToken") or token_data.get("access_token")
        print("Token alındı. Boyut:", len(token) if token else 0)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        endpoints = [
            "/Category",
            "/category",
            "/categories",
            "/Categories",
            "/api/Category",
            "/api/category",
            "/api/Categories",
            "/api/categories",
            "/Category/getCategoryTree",
            "/Category/GetCategoryTree",
            "/Category/GetCategories",
            "/Category/getCategories",
            "/category/category-tree",
            "/category/categoryTree",
            "/api/v1/Category",
            "/api/v1/category",
            "/Category/getAll",
            "/category/getAll",
            "/product/category",
            "/product/categories",
            "/Category/getCategoryWithAttributes",
            "/category/getCategoryWithAttributes",
            "/Category/get-categories"
        ]
        
        for ep in endpoints:
            url = f"https://isortagimapi.pazarama.com{ep}"
            try:
                r = await client.get(url, headers=headers)
                print(f"GET {ep} -> {r.status_code}")
                if r.status_code == 200:
                    print(f"BAŞARILI!: {url}")
                    # Sadece ilk 200 karakteri yazdırıp çıkalım
                    print(r.text[:200])
                    break
            except Exception as e:
                print(f"GET {ep} -> Hata: {e}")

if __name__ == "__main__":
    asyncio.run(main())
