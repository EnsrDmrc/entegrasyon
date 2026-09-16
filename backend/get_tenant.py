import asyncio
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.tenant import Tenant

async def f():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Tenant).where(Tenant.id==13))
        print(res.scalars().first().name)

if __name__ == "__main__":
    asyncio.run(f())
