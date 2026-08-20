from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import asyncio

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.integration import MarketplaceIntegration
from models.product import Product
from models.inventory import Inventory
from schemas.integration import IntegrationCreate, IntegrationResponse
from services.marketplace import ShopifyAdapter, N11Adapter

router = APIRouter()

@router.post("/sync/shopify")
async def sync_shopify(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 1. Tenant'ın Shopify entegrasyonunu bul
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "shopify",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Shopify entegrasyonu bulunamadı.")

    # 2. Ürünleri Çek
    adapter = ShopifyAdapter(api_key=str(integration.api_key), store_url=str(integration.store_url))
    fetched_items = adapter.fetch_all_products()

    if not fetched_items:
        return {"message": "Shopify'da çekilecek ürün (veya SKU'ya sahip varyant) bulunamadı.", "count": 0}

    # 3. Veritabanı Güncelleme İşlemi
    sync_count = 0
    for item in fetched_items:
        # Ürünü SKU ile ara (Tenant bazlı izolasyon)
        prod_result = await db.execute(
            select(Product).where(
                Product.sku == item["sku"], 
                Product.tenant_id == current_user.tenant_id
            )
        )
        product = prod_result.scalars().first()

        if not product:
            # Yeni Ürün Ekle
            product = Product(
                tenant_id=current_user.tenant_id,
                name=item["name"],
                sku=item["sku"],
                price=item["price"]
            )
            db.add(product)
            await db.commit()
            await db.refresh(product)
        else:
            # Ürün zaten varsa ismini ve fiyatını da Shopify'dan güncelleyelim
            product.name = item["name"]
            product.price = item["price"]
            db.add(product)
            await db.commit()

        # Stok tablosunu (Inventory) güncelle/ekle
        inv_result = await db.execute(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.marketplace == "shopify"
            )
        )
        inventory = inv_result.scalars().first()

        if inventory:
            inventory.quantity = item["quantity"]
        else:
            new_inv = Inventory(
                product_id=product.id,
                marketplace="shopify",
                quantity=item["quantity"]
            )
            db.add(new_inv)
        
        await db.commit()
        sync_count += 1

    # Sipariş tarafı yeni endpoint'e taşındı.
    return {"message": "Ürünler başarıyla senkronize edildi", "count": sync_count}

@router.post("/sync/shopify/orders")
async def sync_shopify_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "shopify",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Shopify entegrasyonu bulunamadı.")

    adapter = ShopifyAdapter(api_key=str(integration.api_key), store_url=str(integration.store_url))
    fetched_orders = adapter.fetch_orders()
    from models.order import Order, OrderItem
    from dateutil import parser
    
    order_sync_count = 0
    for ord_data in fetched_orders:
        ord_result = await db.execute(
            select(Order).where(
                Order.order_number == ord_data["order_number"],
                Order.tenant_id == current_user.tenant_id
            )
        )
        existing_order = ord_result.scalars().first()
        
        parsed_date = None
        if ord_data["order_date"]:
            try:
                parsed_date = parser.parse(ord_data["order_date"])
            except:
                pass

        if not existing_order:
            new_order = Order(
                tenant_id=current_user.tenant_id,
                marketplace="shopify",
                order_number=ord_data["order_number"],
                customer_name=ord_data["customer_name"],
                total_price=ord_data["total_price"],
                status=ord_data["status"],
                order_date=parsed_date
            )
            db.add(new_order)
            await db.commit()
            await db.refresh(new_order)
            
            for item in ord_data["items"]:
                new_item = OrderItem(
                    order_id=new_order.id,
                    product_sku=item["product_sku"],
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
                db.add(new_item)
            await db.commit()
            order_sync_count += 1
        else:
            if existing_order.status != ord_data["status"]:
                existing_order.status = ord_data["status"]
                db.add(existing_order)
                await db.commit()
                order_sync_count += 1

    return {
        "message": "Siparişler başarıyla çekildi", 
        "order_count": order_sync_count
    }

@router.post("/sync/n11")
async def sync_n11(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "n11",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.api_secret:
        raise HTTPException(status_code=400, detail="Aktif N11 entegrasyonu bulunamadı.")

    adapter = N11Adapter(api_key=str(integration.api_key), api_secret=str(integration.api_secret))
    try:
        fetched_items = await asyncio.to_thread(adapter.fetch_all_products)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not fetched_items:
        return {"message": "N11'de çekilecek ürün bulunamadı.", "count": 0}

    sync_count = 0
    for item in fetched_items:
        # Ürünü SKU ile ara (Tekilleştirme / Deduplication)
        prod_result = await db.execute(
            select(Product).where(
                Product.sku == item["sku"], 
                Product.tenant_id == current_user.tenant_id
            )
        )
        product = prod_result.scalars().first()

        if not product:
            # Yeni Ürün Ekle
            product = Product(
                tenant_id=current_user.tenant_id,
                name=item["name"],
                sku=item["sku"],
                price=item["price"]
            )
            db.add(product)
            await db.commit()
            await db.refresh(product)
        else:
            # Sadece N11 fiyatını kullanarak ana ürünü güncellemeyelim, stok mappingi önemli.
            # Veritabanında ürün olduğu için pas geçiyoruz, stok Inventory tablosunda güncellenecek.
            pass

        # N11 stok kaydını oluştur
        inv_result = await db.execute(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.marketplace == "n11"
            )
        )
        inventory = inv_result.scalars().first()

        if inventory:
            inventory.quantity = item["quantity"]
        else:
            new_inv = Inventory(
                product_id=product.id,
                marketplace="n11",
                quantity=item["quantity"]
            )
            db.add(new_inv)
        
        await db.commit()
        sync_count += 1

    return {"message": "N11 ürünleri başarıyla senkronize edildi", "count": sync_count}

@router.post("/sync/n11/orders")
async def sync_n11_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "n11",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.api_secret:
        raise HTTPException(status_code=400, detail="Aktif N11 entegrasyonu bulunamadı.")

    adapter = N11Adapter(api_key=str(integration.api_key), api_secret=str(integration.api_secret))
    try:
        fetched_orders = await asyncio.to_thread(adapter.fetch_orders)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    from models.order import Order, OrderItem
    from dateutil import parser
    
    order_sync_count = 0
    for ord_data in fetched_orders:
        ord_result = await db.execute(
            select(Order).where(
                Order.order_number == ord_data["order_number"],
                Order.tenant_id == current_user.tenant_id
            )
        )
        existing_order = ord_result.scalars().first()
        
        parsed_date = None
        if ord_data["order_date"]:
            try:
                parsed_date = parser.parse(ord_data["order_date"])
            except:
                pass

        if not existing_order:
            new_order = Order(
                tenant_id=current_user.tenant_id,
                marketplace="n11",
                order_number=ord_data["order_number"],
                customer_name=ord_data["customer_name"],
                total_price=ord_data["total_price"],
                status=ord_data["status"],
                order_date=parsed_date
            )
            db.add(new_order)
            await db.commit()
            await db.refresh(new_order)
            
            for item in ord_data["items"]:
                new_item = OrderItem(
                    order_id=new_order.id,
                    product_sku=item["product_sku"],
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
                db.add(new_item)
            await db.commit()
            order_sync_count += 1
        else:
            if existing_order.status != ord_data["status"]:
                existing_order.status = ord_data["status"]
                db.add(existing_order)
                await db.commit()
                order_sync_count += 1

    return {
        "message": "N11 Siparişleri başarıyla çekildi", 
        "order_count": order_sync_count
    }

@router.get("", response_model=List[IntegrationResponse])
@router.get("/", response_model=List[IntegrationResponse])
async def get_integrations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(MarketplaceIntegration.tenant_id == current_user.tenant_id)
    )
    return result.scalars().all()

@router.post("", response_model=IntegrationResponse)
@router.post("/", response_model=IntegrationResponse)
async def save_integration(
    data: IntegrationCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Önce bu pazaryeri için daha önce kayıt var mı kontrol et
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == data.marketplace_name
        )
    )
    existing = result.scalars().first()

    if existing:
        # Güncelle (IDE Tip uyarılarını önlemek için setattr kullanıyoruz)
        if data.api_key is not None:
            setattr(existing, 'api_key', data.api_key)
        if data.api_secret is not None:
            setattr(existing, 'api_secret', data.api_secret)
        if data.store_url is not None:
            setattr(existing, 'store_url', data.store_url)
        setattr(existing, 'is_active', data.is_active)
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        # Yeni oluştur
        new_integration = MarketplaceIntegration(
            tenant_id=current_user.tenant_id,
            marketplace_name=data.marketplace_name,
            api_key=data.api_key,
            api_secret=data.api_secret,
            store_url=data.store_url,
            is_active=data.is_active
        )
        db.add(new_integration)
        await db.commit()
        await db.refresh(new_integration)
        return new_integration
