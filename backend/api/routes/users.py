from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from core.database import get_db
from core.security import pwd_context
from api.deps import get_current_user
from models.user import User
from models.tenant import Tenant
from models.product import Product
from schemas import UserResponse, PasswordChange, ProductResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # İlişkili tenant'ı da yükleyebiliriz veya basitçe:
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalars().first()
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "tenant_id": current_user.tenant_id,
        "tenant": tenant
    }

@router.get("/me/products", response_model=List[ProductResponse])
async def get_my_products(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Sadece giriş yapan kullanıcının tenant'ına ait ürünleri getir (Multi-tenant izolasyonu)
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Product)
        .where(Product.tenant_id == current_user.tenant_id)
        .options(selectinload(Product.inventories))
    )
    products = result.scalars().all()
    return products

from schemas.schemas import ProductUpdateRequest
from models.integration import MarketplaceIntegration
from services.marketplace import ShopifyAdapter, N11Adapter
import asyncio

@router.put("/me/products/{product_id}")
async def update_product(
    product_id: int,
    data: ProductUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from models.inventory import Inventory
    
    # Güvenlik kontrolü: Ürün bu tenant'a mı ait?
    prod_result = await db.execute(
        select(Product).where(Product.id == product_id, Product.tenant_id == current_user.tenant_id)
    )
    product = prod_result.scalars().first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    # Fiyat Güncellemesi
    if data.price is not None:
        product.price = data.price
        db.add(product)

    # Envanter (Stok) Güncellemesi
    if data.quantity is not None:
        inv_result = await db.execute(
            select(Inventory).where(Inventory.product_id == product.id)
        )
        inventories = inv_result.scalars().all()
        
        if not inventories:
            new_inv = Inventory(product_id=product.id, marketplace="manual", quantity=data.quantity)
            db.add(new_inv)
        else:
            for inv in inventories:
                inv.quantity = data.quantity
                db.add(inv)
                
    await db.commit()

    # Değişiklikleri Shopify'a Push Et (Senkronizasyon)
    if data.price is not None or data.quantity is not None:
        int_result = await db.execute(
            select(MarketplaceIntegration)
            .where(
                MarketplaceIntegration.tenant_id == current_user.tenant_id,
                MarketplaceIntegration.marketplace_name == "shopify",
                MarketplaceIntegration.is_active == True
            )
        )
        integration = int_result.scalars().first()

        if integration and integration.api_key and integration.store_url:
            adapter = ShopifyAdapter(api_key=str(integration.api_key), store_url=str(integration.store_url))
            # Hata yapsa bile bizim DB'miz güncellendi, sadece logluyoruz
            await asyncio.to_thread(
                adapter.update_product,
                sku=product.sku, 
                new_price=data.price, 
                new_stock=data.quantity
            )
            
        # N11'e Push Et
        n11_result = await db.execute(
            select(MarketplaceIntegration)
            .where(
                MarketplaceIntegration.tenant_id == current_user.tenant_id,
                MarketplaceIntegration.marketplace_name == "n11",
                MarketplaceIntegration.is_active == True
            )
        )
        n11_int = n11_result.scalars().first()
        
        if n11_int and n11_int.api_key and n11_int.api_secret:
            n11_adapter = N11Adapter(api_key=str(n11_int.api_key), api_secret=str(n11_int.api_secret))
            await asyncio.to_thread(
                n11_adapter.update_product,
                sku=product.sku,
                new_price=data.price,
                new_stock=data.quantity
            )

        sync_results = {}
        
        # Hepsiburada'ya Push Et
        hb_result = await db.execute(
            select(MarketplaceIntegration)
            .where(
                MarketplaceIntegration.tenant_id == current_user.tenant_id,
                MarketplaceIntegration.marketplace_name == "hepsiburada",
                MarketplaceIntegration.is_active == True
            )
        )
        hb_int = hb_result.scalars().first()
        
        if hb_int and hb_int.api_key and hb_int.store_url:
            from services.marketplace import HepsiburadaAdapter
            store_url = str(hb_int.store_url)
            is_test = store_url.endswith("|test")
            real_merchant_id = store_url.replace("|test", "")
            hb_adapter = HepsiburadaAdapter(merchant_id=real_merchant_id, api_key=str(hb_int.api_key), is_test=is_test)
            
            try:
                hb_success, hb_msg = await asyncio.to_thread(
                    hb_adapter.update_product,
                    sku=product.sku,
                    new_price=data.price,
                    new_stock=data.quantity
                )
                sync_results["hepsiburada"] = {"success": hb_success, "message": str(hb_msg)}
            except Exception as e:
                sync_results["hepsiburada"] = {"success": False, "message": str(e)}

        # Pazarama'ya Push Et
        pazarama_result = await db.execute(
            select(MarketplaceIntegration)
            .where(
                MarketplaceIntegration.tenant_id == current_user.tenant_id,
                MarketplaceIntegration.marketplace_name == "pazarama",
                MarketplaceIntegration.is_active == True
            )
        )
        pazarama_int = pazarama_result.scalars().first()
        
        if pazarama_int and pazarama_int.api_key and pazarama_int.store_url:
            from services.marketplace import PazaramaAdapter
            p_adapter = PazaramaAdapter(merchant_id=str(pazarama_int.store_url), api_key=str(pazarama_int.api_key), api_secret=str(pazarama_int.api_secret) if pazarama_int.api_secret else None)
            
            # Pazarama sadece ürün ekleme servisiyle (upsert) fiyat/stok güncelleyebiliyor
            import json
            product_data = {
                "name": product.name,
                "description": getattr(product, "description", product.name),
                "sku": product.sku,
                "stock": data.quantity,
                "price": data.price,
                "images": json.loads(product.images_json) if getattr(product, "images_json", None) else [{"imageurl": "https://via.placeholder.com/500"}]
            }
            
            target_category_id = str(getattr(product, "pazarama_category_id") or "")
            target_brand_id = str(getattr(product, "pazarama_brand_id") or "")
            
            if target_category_id and target_category_id != "0" and target_brand_id and target_brand_id != "0":
                await asyncio.to_thread(
                    p_adapter.create_product,
                    product_data=product_data,
                    target_category_id=target_category_id,
                    target_brand_id=target_brand_id,
                    vat_rate=20
                )
            else:
                print(f"[Pazarama] Kategori/Marka ID bulunamadığı için atlandı: {product.sku}")

    return {"message": "Ürün başarıyla güncellendi", "sync_results": sync_results}

@router.get("/debug-pazarama")
async def debug_pazarama(sku: str, stock: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "pazarama", MarketplaceIntegration.is_active == True))
    p_int = result.scalars().first()
    if not p_int: return {"error": "no pazarama int"}
    from services.marketplace import PazaramaAdapter
    adapter = PazaramaAdapter(merchant_id=str(p_int.store_url), api_key=str(p_int.api_key), api_secret=str(p_int.api_secret))
    adapter._get_token()
    import httpx
    headers = {"Authorization": f"Bearer {adapter.token}", "Accept": "application/json"}
    
    results = {}
    
    # 1. Array payload
    try:
        r1 = httpx.post("https://isortagimapi.pazarama.com/product/updateStock", headers=headers, json=[{"Code": sku, "StockCount": stock}], timeout=10.0)
        results["format1"] = f"{r1.status_code} - {r1.text[:200]}"
    except Exception as e: results["format1"] = str(e)
    
    # 2. Object payload
    try:
        r2 = httpx.post("https://isortagimapi.pazarama.com/product/updateStock", headers=headers, json={"Code": sku, "StockCount": stock}, timeout=10.0)
        results["format2"] = f"{r2.status_code} - {r2.text[:200]}"
    except Exception as e: results["format2"] = str(e)
    
    # 3. Uppercase endpoint
    try:
        r3 = httpx.post("https://isortagimapi.pazarama.com/Product/UpdateStock", headers=headers, json=[{"Code": sku, "StockCount": stock}], timeout=10.0)
        results["format3"] = f"{r3.status_code} - {r3.text[:200]}"
    except Exception as e: results["format3"] = str(e)
    
    # 4. products wrapper
    try:
        r4 = httpx.post("https://isortagimapi.pazarama.com/product/updateStock", headers=headers, json={"products": [{"Code": sku, "StockCount": stock}]}, timeout=10.0)
        results["format4"] = f"{r4.status_code} - {r4.text[:200]}"
    except Exception as e: results["format4"] = str(e)

    # 5. Get Products to check if sku exists
    try:
        r5 = httpx.get("https://isortagimapi.pazarama.com/product/products?Approved=True&Size=5&Page=1", headers=headers, timeout=10.0)
        if r5.status_code != 200:
            r5 = httpx.get("https://isortagimapi.pazarama.com/product/products/approved?Size=5&Page=1", headers=headers, timeout=10.0)
        data = r5.json()
        items = data.get("items") or data.get("products") or data.get("data") or []
        results["first_sku"] = items[0].get("code") if items else "NONE"
    except Exception as e: results["first_sku_error"] = str(e)
    
    return results

from schemas.order import OrderSchema

@router.get("/me/orders", response_model=List[OrderSchema])
async def get_my_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from models.order import Order
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Order)
        .where(Order.tenant_id == current_user.tenant_id)
        .options(selectinload(Order.items))
        .order_by(Order.order_date.desc())
    )
    orders = result.scalars().all()
    return orders

@router.delete("/me/orders")
async def clear_my_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text
    try:
        # Önce sipariş kalemlerini siliyoruz (Foreign Key kısıtlaması nedeniyle)
        await db.execute(
            text("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE tenant_id = :tenant_id)"),
            {"tenant_id": current_user.tenant_id}
        )
        # Sonra siparişlerin kendisini siliyoruz
        await db.execute(
            text("DELETE FROM orders WHERE tenant_id = :tenant_id"),
            {"tenant_id": current_user.tenant_id}
        )
        await db.commit()
        return {"message": "Tüm geçmiş sipariş kayıtları başarıyla silindi!"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Siparişler silinirken hata oluştu: {str(e)}")
