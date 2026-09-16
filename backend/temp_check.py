import asyncio
import sys
sys.path.append('./backend')
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.product import Product

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Product).where(Product.sku.contains('yld14x15')))
        p = res.scalars().first()
        if p:
            print(f"URL: {p.n11_url}")
            print(f"COMPETITORS: {p.competitors_json}")
        else:
            print('Not found')

asyncio.run(check())
