import asyncio
import sys
sys.path.append('./backend')
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models.order import Order

async def get_orders():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Order).options(selectinload(Order.items)).order_by(Order.order_date.desc()).limit(10))
        orders = res.scalars().all()
        for o in orders:
            print(f"Order: {o.order_number}, Market: {o.marketplace}, Date: {o.order_date}")
            for i in o.items:
                print(f"  Item: {i.product_sku} - {i.product_name} x {i.quantity}")

if __name__ == "__main__":
    asyncio.run(get_orders())
