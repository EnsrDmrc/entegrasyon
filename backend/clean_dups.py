import asyncio
import sys
sys.path.append('./backend')
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.product import Product

async def clean_duplicates():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Product))
        products = res.scalars().all()
        
        sku_map = {}
        duplicates = []
        for p in products:
            if p.sku in sku_map:
                duplicates.append(p)
            else:
                sku_map[p.sku] = p
                
        print(f"Found {len(duplicates)} duplicates out of {len(products)} products.")
        
        for d in duplicates:
            print(f"Deleting duplicate SKU: {d.sku} (ID: {d.id})")
            await db.delete(d)
            
        await db.commit()
        print("Duplicates deleted successfully.")

if __name__ == "__main__":
    asyncio.run(clean_duplicates())
