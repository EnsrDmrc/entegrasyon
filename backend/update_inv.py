import asyncio
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.inventory import Inventory

async def update_inv():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Inventory).where(Inventory.product_id == 134, Inventory.marketplace == "n11"))
        inv = res.scalars().first()
        if inv:
            inv.quantity = 10
            db.add(inv)
        else:
            new_inv = Inventory(product_id=134, marketplace="n11", quantity=10)
            db.add(new_inv)
        await db.commit()
        print("Inventory updated!")

if __name__ == "__main__":
    asyncio.run(update_inv())
