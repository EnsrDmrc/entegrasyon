import asyncio
import sys
sys.path.append('./backend')
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.product import Product
from models.tenant import Tenant

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Product).where(Product.last_repricing_check != None))
        products = res.scalars().all()
        print(f"Products with last_repricing_check != None: {len(products)}")
        if products:
            p = products[0]
            print(f"Sample: SKU={p.sku}, URL={p.n11_url}, is_expensive={p.is_expensive}, competitors={p.competitors_json}")

asyncio.run(check())
