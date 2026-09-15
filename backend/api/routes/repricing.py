from fastapi import APIRouter, BackgroundTasks
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.user import User
from models.tenant import Tenant
from fastapi import Depends, HTTPException
from api.deps import get_current_user

router = APIRouter()

@router.post("/n11/trigger")
async def trigger_n11_repricing(background_tasks: BackgroundTasks):
    """
    Sisteme kaydedilmiş olan N11 ürünlerinin rakip fiyatlarını analiz edip,
    kârı maksimize edecek şekilde fiyatları güncelleyen 'Repricing' algoritmasını manuel tetikler.
    (Normalde bu işlem her gece 03:00'da otomatik çalışır.)
    """
    from services.repricing import run_n11_repricing
    
    # Sadece yetkili kullanıcıların veya test için adminin tetikleyebilmesi için (Şimdilik izin veriyoruz)
    background_tasks.add_task(run_n11_repricing)
    
    return {
        "message": "N11 Otomatik Fiyatlandırma (Repricing) arka planda başlatıldı. Terminal loglarından süreci takip edebilirsiniz."
    }

@router.get("/debug")
async def debug_repricing_state():
    from models.integration import MarketplaceIntegration
    from models.product import Product
    from models.tenant import Tenant
    async with AsyncSessionLocal() as db:
        ints_res = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "n11", MarketplaceIntegration.is_active == True))
        ints = ints_res.scalars().all()
        
        result = {"integrations": []}
        for i in ints:
            tenant_res = await db.execute(select(Tenant).where(Tenant.id == i.tenant_id))
            tenant = tenant_res.scalars().first()
            
            prods_res = await db.execute(select(Product).where(Product.tenant_id == i.tenant_id, Product.n11_url != None))
            prods = prods_res.scalars().all()
            
            all_prods_res = await db.execute(select(Product).where(Product.tenant_id == i.tenant_id))
            all_prods = all_prods_res.scalars().all()
            
            result["integrations"].append({
                "tenant_id": i.tenant_id,
                "tenant_name": tenant.name if tenant else None,
                "products_with_n11_url": [{"sku": p.sku, "url": p.n11_url} for p in prods],
                "total_products": len(all_prods)
            })
            
        return result

@router.get("/expensive-products")
async def get_expensive_products(current_user: User = Depends(get_current_user)):
    """
    Kullanıcının tenant'ına ait, son otomatik fiyatlandırma kontrolünde "Pahalı" olarak işaretlenmiş
    (yani en ucuz rakibin fiyatının altında kalamamış veya rakip fiyatı çok düşürdüğü için kural gereği dokunulmamış)
    ürünlerin listesini getirir.
    """
    from models.product import Product
    async with AsyncSessionLocal() as db:
        query = select(Product).where(
            Product.tenant_id == current_user.tenant_id,
            Product.is_expensive == 1
        )
        result = await db.execute(query)
        products = result.scalars().all()
        
        return {
            "isSuccess": True,
            "data": [
                {
                    "sku": p.sku,
                    "name": p.name,
                    "our_price": p.price,
                    "cheapest_competitor_name": p.cheapest_competitor_name,
                    "cheapest_competitor_price": p.cheapest_competitor_price,
                    "last_checked": p.last_repricing_check
                }
                for p in products
            ]
        }
