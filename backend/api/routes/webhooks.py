from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from core.locking import distributed_lock
from models.inventory import Inventory
from tasks import sync_inventory
from pydantic import BaseModel

router = APIRouter()

class OrderPayload(BaseModel):
    product_id: int
    quantity_bought: int
    marketplace: str

@router.post("/shopify/order_created")
async def shopify_order_webhook(payload: OrderPayload, db: AsyncSession = Depends(get_db)):
    """
    Shopify'dan yeni bir sipariş geldiğinde tetiklenir.
    Redis lock kullanarak aynı anda iki siparişin over-selling yapmasını engeller.
    """
    lock_name = f"product_inventory_{payload.product_id}"
    
    try:
        # Stoğu kilitliyoruz (Başka bir pazar yeri aynı anda satamasın diye)
        async with distributed_lock(lock_name, timeout=5, sleep_time=0.1):
            
            # 1. Stoğu veritabanından oku
            result = await db.execute(select(Inventory).where(Inventory.product_id == payload.product_id))
            inventory = result.scalars().first()
            
            if not inventory:
                raise HTTPException(status_code=404, detail="Inventory not found")
                
            if inventory.quantity < payload.quantity_bought:
                # Gerçek hayatta burada sipariş iptal edilir veya eksi stoğa düşülür (iş modeline göre)
                raise HTTPException(status_code=400, detail="Not enough stock! Over-selling prevented.")
                
            # 2. Stoğu düşür ve kaydet
            inventory.quantity -= payload.quantity_bought  # type: ignore
            db.add(inventory)
            await db.commit()
            
            # 3. Arka plan görevini (Celery) tetikle. 
            # Shopify'da satıldı, n11 ve diğer pazaryerlerine senkronize et.
            sync_inventory.delay(
                product_id=inventory.product_id, 
                new_quantity=inventory.quantity, 
                origin_marketplace=payload.marketplace
            )
            
            return {"message": "Stock updated and sync task queued", "new_quantity": inventory.quantity}
            
    except TimeoutError:
        raise HTTPException(status_code=429, detail="System is busy processing another order for this item. Please try again.")
