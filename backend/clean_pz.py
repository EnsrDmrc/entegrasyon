import asyncio
import os
import sys
sys.path.append('./backend')
from core.database import AsyncSessionLocal
from models.order import Order, OrderItem
from sqlalchemy import select, delete

async def clean():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Order.id).where(Order.order_number.like("PZ-%")))
        ids = [r[0] for r in res.all()]
        print(f"Found {len(ids)} fake orders")
        if ids:
            await db.execute(delete(OrderItem).where(OrderItem.order_id.in_(ids)))
            await db.execute(delete(Order).where(Order.id.in_(ids)))
            await db.commit()
            print("Cleaned fake orders")

if __name__ == "__main__":
    asyncio.run(clean())
