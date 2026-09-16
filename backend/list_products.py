import asyncio
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.tenant import Tenant
from models.integration import MarketplaceIntegration
from models.inventory import Inventory

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Tenant))
        tenants = res.scalars().all()
        for t in tenants:
            print(f"Tenant ID: {t.id}, Name: {t.name}")
            
            # Change name to saygingrup if it's the first one, just to ensure match!
            if t.id == 1:
                t.name = "Saygın Grup"
                db.add(t)
        
        await db.commit()

if __name__ == "__main__":
    asyncio.run(main())
