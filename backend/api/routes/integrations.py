from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
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

@router.post("/test-shopify")
async def test_shopify(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "shopify",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Aktif Shopify entegrasyonu bulunamadı")
        
    try:
        from services.marketplace import ShopifyAdapter
        adapter = ShopifyAdapter(api_key=str(integration.api_key), store_url=str(integration.store_url))
        orders = await asyncio.to_thread(adapter.fetch_orders)
        return {"status": "success", "orders_fetched": len(orders), "sample": orders[:2] if orders else []}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/n11-force-sync/{order_number}")
async def n11_force_sync(order_number: str, db: AsyncSession = Depends(get_db)):
    # Tekil siparişi doğrudan N11 OrderDetail API üzerinden zorla eşitleyen uç (Geçici yetkisiz)
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.marketplace_name == "n11",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()
    if not integration:
        raise HTTPException(status_code=404, detail="Aktif N11 entegrasyonu bulunamadı")
        
    from zeep import Client
    from zeep.transports import Transport
    from requests import Session
    from models.order import Order
    
    auth = {'appKey': integration.api_key, 'appSecret': integration.api_secret}
    transport = Transport(session=Session())
    client = Client('https://api.n11.com/ws/OrderService.wsdl', transport=transport)
    
    try:
        # Önce sipariş numarasıyla arama yapıp N11'in iç ID'sini bulmalıyız
        import datetime
        end_d = datetime.datetime.now()
        start_d = end_d - datetime.timedelta(days=180)
        search_data = {
            'orderNumber': order_number,
            'period': {
                'startDate': start_d.strftime('%d/%m/%Y 00:00'),
                'endDate': end_d.strftime('%d/%m/%Y 23:59')
            }
        }
        paging = {'currentPage': 0, 'pageSize': 10}
        list_res = client.service.OrderList(auth=auth, searchData=search_data, pagingData=paging)
        
        if list_res.result.status == "failure" or not hasattr(list_res, 'orderList') or not list_res.orderList.order:
            return {"error": "N11 OrderList siparişi bulamadı", "raw": str(list_res.result)}
            
        n11_order_id = list_res.orderList.order[0].id
        
        # Şimdi gerçek iç ID ile detayları çek
        detail_res = client.service.OrderDetail(auth=auth, orderRequest={'id': n11_order_id})
        if detail_res.result.status == "failure" or not hasattr(detail_res, 'orderDetail'):
            return {"error": "N11 OrderDetail api çağrısı başarısız", "raw": str(detail_res.result)}
            
        ord_data = detail_res.orderDetail
        raw_status = str(ord_data.status) if hasattr(ord_data, 'status') else "bilinmiyor"
        
        status_map = {
            "1": "Onay Bekliyor",
            "2": "Onaylandı",
            "3": "Reddedildi",
            "4": "Kargolandı",
            "5": "Teslim Edildi",
            "6": "Tamamlandı",
            "7": "İade Edildi",
            "8": "İptal Edildi"
        }
        mapped_status = status_map.get(raw_status, raw_status)
        
        # DB'de güncelle
        ord_result = await db.execute(select(Order).where(Order.order_number == order_number, Order.tenant_id == integration.tenant_id))
        existing = ord_result.scalars().first()
        
        updated = False
        old_status = None
        if existing:
            old_status = existing.status
            if existing.status != mapped_status:
                existing.status = mapped_status
                db.add(existing)
                await db.commit()
                updated = True
                
        return {
            "order_number": order_number,
            "n11_raw_status": raw_status,
            "mapped_status": mapped_status,
            "old_db_status": old_status,
            "updated_in_db": updated,
            "raw_api_data": str(ord_data)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@router.post("/sync/push-n11-stocks")
async def push_n11_stocks_to_shopify(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 1. Shopify entegrasyonunu bul
    shopify_result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "shopify",
            MarketplaceIntegration.is_active == True
        )
    )
    shopify_int = shopify_result.scalars().first()
    if not shopify_int or not shopify_int.api_key or not shopify_int.store_url:
        raise HTTPException(status_code=400, detail="Shopify entegrasyonu bulunamadı.")
        
    s_adapter = ShopifyAdapter(api_key=str(shopify_int.api_key), store_url=str(shopify_int.store_url))
    
    # 2. Ürünleri ve N11 stoklarını bul
    products_result = await db.execute(select(Product).where(Product.tenant_id == current_user.tenant_id))
    products = products_result.scalars().all()
    
    async def run_push():
        from core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            success_count = 0
            for prod in products:
                inv_res = await session.execute(
                    select(Inventory).where(Inventory.product_id == prod.id, Inventory.marketplace == "n11")
                )
                inv = inv_res.scalars().first()
                if inv:
                    try:
                        # API'ye pushla
                        await asyncio.to_thread(s_adapter.update_product, prod.sku, None, inv.quantity)
                        
                        # Veritabanında Shopify stok kaydını da güncelle
                        shop_inv_res = await session.execute(
                            select(Inventory).where(Inventory.product_id == prod.id, Inventory.marketplace == "shopify")
                        )
                        shop_inv = shop_inv_res.scalars().first()
                        if shop_inv:
                            shop_inv.quantity = inv.quantity
                        else:
                            new_shop_inv = Inventory(
                                product_id=prod.id,
                                marketplace="shopify",
                                quantity=inv.quantity
                            )
                            session.add(new_shop_inv)
                        
                        await session.commit()
                        success_count += 1
                    except Exception as e:
                        print(f"Shopify stock push error for {prod.sku}: {e}")
            print(f"Background Sync Finished: {success_count} items pushed to Shopify.")

    background_tasks.add_task(run_push)
    return {"message": "Stoklar arka planda Shopify'a aktarılmaya başlandı! Yaklaşık 2-3 dakika içinde tamamlanacaktır."}

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
                parsed_date = parser.parse(ord_data["order_date"], dayfirst=True)
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
