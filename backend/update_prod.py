import asyncio
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.product import Product

async def update_prod():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Product).where(Product.id == 134))
        prod = res.scalars().first()
        if prod:
            prod.n11_url = "https://www.n11.com/urun/yildiz-iki-agiz-anahtar-14x15-130617729?magaza=saygingrup"
            prod.price = 1350.0
            db.add(prod)
            await db.commit()
            print("Product updated successfully!")
        else:
            print("Product not found!")

if __name__ == "__main__":
    asyncio.run(update_prod())
