import asyncio
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.product import Product

async def find_prod():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Product).where(Product.name.ilike('%yildiz%') | Product.name.ilike('%yıldız%') | Product.name.ilike('%anahtar%')))
        prods = res.scalars().all()
        for p in prods:
            print(f"ID: {p.id}, Tenant: {p.tenant_id}, SKU: {p.sku}, Name: {p.name}, Price: {p.price}")

if __name__ == "__main__":
    asyncio.run(find_prod())
