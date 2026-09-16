import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import engine, AsyncSessionLocal
from models.integration import MarketplaceIntegration

from zeep import Client
from zeep.helpers import serialize_object

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "n11"))
        integration = result.scalars().first()
        if not integration or not integration.api_key:
            print("N11 integration not found in DB.")
            return

        api_key = integration.api_key
        api_secret = integration.api_secret
        
        wsdl = 'https://api.n11.com/ws/ProductService.wsdl'
        client = Client(wsdl=wsdl)
        
        auth = {
            'appKey': api_key,
            'appSecret': api_secret
        }
        
        try:
            print("Sending GetProductBySellerCode via zeep...")
            response = client.service.GetProductBySellerCode(
                auth=auth,
                sellerCode="crc12"
            )
            print("Response status:", response.result.status)
            if response.result.status == 'failure':
                print("Error Message:", response.result.errorMessage)
            else:
                print("Success! Product:", serialize_object(response.product))
        except Exception as e:
            print("Zeep exception:", e)

if __name__ == "__main__":
    asyncio.run(main())
