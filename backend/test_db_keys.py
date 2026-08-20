import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import engine, AsyncSessionLocal
from models.integration import MarketplaceIntegration

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "n11"))
        integration = result.scalars().first()
        if not integration or not integration.api_key:
            print("N11 integration not found in DB.")
            return

        api_key = integration.api_key
        api_secret = integration.api_secret
        
        print("RAW API KEY:")
        print(repr(api_key))
        print("RAW API SECRET:")
        print(repr(api_secret))

if __name__ == "__main__":
    asyncio.run(main())
