import asyncio
from services.marketplace import PazaramaAdapter
from core.config import settings

async def main():
    # Use real credentials or user's environment. Actually I'll just use the DB to fetch credentials.
    from core.database import SessionLocal
    from models.integration import MarketplaceIntegration

    db = SessionLocal()
    integration = db.query(MarketplaceIntegration).filter_by(marketplace="pazarama").first()
    if not integration:
        print("Pazarama entegrasyonu bulunamadı.")
        return

    adapter = PazaramaAdapter(
        seller_id=integration.seller_id,
        refresh_token=integration.api_secret or integration.api_key # The password/token is usually in api_secret
    )
    
    # Just try to send a test product
    test_products = [
        {
            "Name": "Test Product Pazarama Debug",
            "DisplayName": "Test Product Pazarama Debug",
            "Description": "Test açıklama",
            "BrandId": "23d1cb53-06a1-4fc3-a9d3-0d2966f91757", # Some dummy guid
            "CategoryId": "3497d3dc-de4c-4ddf-aeaf-12dce0220671", # Some dummy guid
            "Code": "DEBUG-SKU-001",
            "GroupCode": "DEBUG-SKU-001",
            "StockCount": 10,
            "VatRate": 20,
            "ListPrice": 100.0,
            "SalePrice": 100.0,
            "Desi": 1,
            "images": [{"imageurl": "https://via.placeholder.com/500"}]
        }
    ]
    
    try:
        res = adapter.create_products_bulk(test_products)
        print("BULK RESPONSE:", res)
    except Exception as e:
        print("EXCEPTION:", e)

if __name__ == "__main__":
    asyncio.run(main())
