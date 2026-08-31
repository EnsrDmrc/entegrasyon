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
from schemas.transfer import ProductTransferRequest
from services.marketplace import ShopifyAdapter, N11Adapter

router = APIRouter()

async def push_price_updates_to_others(tenant_id: int, origin_marketplace: str, modified_prices: list):
    if not modified_prices: return
    
    from core.database import AsyncSessionLocal
    from services.marketplace import ShopifyAdapter, N11Adapter, TrendyolAdapter, HepsiburadaAdapter
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MarketplaceIntegration)
            .where(MarketplaceIntegration.tenant_id == tenant_id, MarketplaceIntegration.is_active == True)
        )
        integrations = result.scalars().all()
        
        for integration in integrations:
            if integration.marketplace_name == origin_marketplace:
                continue
                
            adapter = None
            try:
                if integration.marketplace_name == "shopify" and integration.api_key and integration.store_url:
                    adapter = ShopifyAdapter(api_key=str(integration.api_key), store_url=str(integration.store_url))
                elif integration.marketplace_name == "n11" and integration.api_key and integration.api_secret:
                    adapter = N11Adapter(api_key=str(integration.api_key), api_secret=str(integration.api_secret))
                elif integration.marketplace_name == "trendyol" and integration.api_key and integration.api_secret and integration.store_url:
                    adapter = TrendyolAdapter(supplier_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret))
                elif integration.marketplace_name == "hepsiburada" and integration.api_key and integration.store_url:
                    adapter = HepsiburadaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key))
                elif integration.marketplace_name == "pazarama" and integration.api_key and integration.store_url:
                    from services.marketplace import PazaramaAdapter
                    adapter = PazaramaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret) if integration.api_secret else None)
                elif integration.marketplace_name == "amazon" and integration.api_key and integration.store_url:
                    from core.config import settings
                    from services.marketplace import AmazonAdapter
                    adapter = AmazonAdapter(
                        refresh_token=str(integration.api_key),
                        seller_id=str(integration.store_url),
                        region=str(integration.api_secret) or "EU",
                        lwa_client_id=settings.AMAZON_LWA_CLIENT_ID,
                        lwa_client_secret=settings.AMAZON_LWA_CLIENT_SECRET
                    )
                    
                if adapter:
                    for sku, new_price in modified_prices:
                        await asyncio.to_thread(adapter.update_product, sku, new_price=new_price)
                        print(f"[Price Sync] Pushed price {new_price} for {sku} to {integration.marketplace_name}")
            except Exception as e:
                print(f"[Price Sync Error] Failed to push to {integration.marketplace_name}: {e}")

@router.get("/active")
async def get_active_integrations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Aktif entegrasyonları döndürür."""
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(MarketplaceIntegration.tenant_id == current_user.tenant_id, MarketplaceIntegration.is_active == True)
    )
    integrations = result.scalars().all()
    return [{"marketplace_name": i.marketplace_name} for i in integrations]


@router.post("/sync/shopify")
async def sync_shopify(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
    modified_prices = []
    
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
            if product.price != float(item["price"]):
                product.price = float(item["price"])
                modified_prices.append((item["sku"], product.price))
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

    if modified_prices:
        background_tasks.add_task(push_price_updates_to_others, current_user.tenant_id, "shopify", modified_prices)

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
        
    from zeep import Client, Settings
    from zeep.transports import Transport
    from requests import Session
    from models.order import Order
    
    auth = {'appKey': integration.api_key, 'appSecret': integration.api_secret}
    transport = Transport(session=Session())
    settings = Settings(strict=False, xsd_ignore_sequence_order=True)
    client = Client('https://api.n11.com/ws/OrderService.wsdl', transport=transport, settings=settings)
    
    try:
        # Önce sipariş numarasıyla arama yapıp N11'in iç ID'sini bulmalıyız
        import datetime
        end_d = datetime.datetime.now()
        start_d = end_d - datetime.timedelta(days=180)
        search_data = {
            'productId': '',
            'status': '',
            'buyerName': '',
            'orderNumber': order_number,
            'productSellerCode': '',
            'recipient': '',
            'sameDayDelivery': '',
            'period': {
                'startDate': start_d.strftime('%d/%m/%Y 00:00'),
                'endDate': end_d.strftime('%d/%m/%Y 23:59')
            },
            'sortForUpdateDate': False,
            'updateDateSortOrder': 'DESC'
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
            "1": "Yeni Sipariş",
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

@router.post("/sync/pazarama")
async def sync_pazarama(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "pazarama",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Pazarama entegrasyonu bulunamadı.")

    from services.marketplace import PazaramaAdapter
    adapter = PazaramaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret) if integration.api_secret else None)
    try:
        fetched_items = await asyncio.to_thread(adapter.fetch_all_products)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not fetched_items:
        return {"message": "Pazarama'da çekilecek ürün bulunamadı.", "count": 0}

    from models.product import Product
    from models.inventory import Inventory
    import json

    sync_count = 0
    modified_prices = []

    for item in fetched_items:
        if not item.get("sku"):
            continue

        prod_result = await db.execute(
            select(Product).where(
                Product.sku == item["sku"],
                Product.tenant_id == current_user.tenant_id
            )
        )
        product = prod_result.scalars().first()

        if not product:
            product = Product(
                tenant_id=current_user.tenant_id,
                sku=item["sku"],
                name=item["name"],
                price=item["price"],
                pazarama_category_id=item.get("category_id"),
                pazarama_brand_id=item.get("brand_id"),
                images_json=json.dumps(item.get("images", [])) if item.get("images") else None
            )
            db.add(product)
            await db.commit()
            await db.refresh(product)
        else:
            product.name = item["name"]
            if product.price != float(item["price"]):
                product.price = float(item["price"])
                modified_prices.append((item["sku"], product.price))
                
            # Gelen metadata verilerini güncelle
            if item.get("category_id"):
                product.pazarama_category_id = item["category_id"]
            if item.get("brand_id"):
                product.pazarama_brand_id = item["brand_id"]
            if item.get("images"):
                product.images_json = json.dumps(item["images"])
                
            db.add(product)
            await db.commit()

        # Stok tablosunu (Inventory) güncelle/ekle
        inv_result = await db.execute(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.marketplace == "pazarama"
            )
        )
        inventory = inv_result.scalars().first()

        if inventory:
            inventory.quantity = item["stock"]
        else:
            new_inv = Inventory(
                product_id=product.id,
                marketplace="pazarama",
                quantity=item["stock"]
            )
            db.add(new_inv)
        
        await db.commit()
        sync_count += 1

    if modified_prices:
        from tasks import push_price_updates_to_others
        background_tasks.add_task(push_price_updates_to_others, current_user.tenant_id, "pazarama", modified_prices)

    return {"message": "Pazarama ürünleri başarıyla çekildi", "count": sync_count}

@router.post("/sync/n11")
async def sync_n11(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
    modified_prices = []
    
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
            if product.price != float(item["price"]):
                product.price = float(item["price"])
                db.add(product)
                await db.commit()
                modified_prices.append((item["sku"], product.price))

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

    if modified_prices:
        background_tasks.add_task(push_price_updates_to_others, current_user.tenant_id, "n11", modified_prices)

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

@router.post("/sync/hepsiburada")
async def sync_hepsiburada(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "hepsiburada",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Hepsiburada entegrasyonu bulunamadı (API Key veya Merchant ID eksik).")

    from services.marketplace import HepsiburadaAdapter
    # api_key -> API Şifresi, store_url -> Merchant ID olarak maplendi
    adapter = HepsiburadaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key))
    try:
        fetched_items = await asyncio.to_thread(adapter.fetch_all_products)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not fetched_items:
        return {"message": "Hepsiburada'da çekilecek ürün bulunamadı.", "count": 0}

    sync_count = 0
    modified_prices = []
    
    for item in fetched_items:
        prod_result = await db.execute(
            select(Product).where(
                Product.sku == item["sku"], 
                Product.tenant_id == current_user.tenant_id
            )
        )
        product = prod_result.scalars().first()

        if not product:
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
            if product.price != float(item["price"]):
                product.price = float(item["price"])
                db.add(product)
                await db.commit()
                modified_prices.append((item["sku"], product.price))

        inv_result = await db.execute(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.marketplace == "hepsiburada"
            )
        )
        inventory = inv_result.scalars().first()

        if inventory:
            inventory.quantity = item["quantity"]
        else:
            new_inv = Inventory(
                product_id=product.id,
                marketplace="hepsiburada",
                quantity=item["quantity"]
            )
            db.add(new_inv)
        
        await db.commit()
        sync_count += 1

    if modified_prices:
        background_tasks.add_task(push_price_updates_to_others, current_user.tenant_id, "hepsiburada", modified_prices)

    return {"message": "Hepsiburada ürünleri başarıyla senkronize edildi", "count": sync_count}


@router.post("/sync/hepsiburada/orders")
async def sync_hepsiburada_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "hepsiburada",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Hepsiburada entegrasyonu bulunamadı.")

    from services.marketplace import HepsiburadaAdapter
    adapter = HepsiburadaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key))
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
                marketplace="hepsiburada",
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
        "message": "Hepsiburada Siparişleri başarıyla çekildi", 
        "order_count": order_sync_count
    }


@router.post("/sync/trendyol")
async def sync_trendyol(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "trendyol",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.api_secret or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Trendyol entegrasyonu bulunamadı (API Key, API Secret veya Satıcı ID eksik).")

    from services.marketplace import TrendyolAdapter
    # store_url -> Satıcı ID (Supplier ID)
    adapter = TrendyolAdapter(supplier_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret))
    try:
        fetched_items = await asyncio.to_thread(adapter.fetch_all_products)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not fetched_items:
        return {"message": "Trendyol'da çekilecek ürün bulunamadı.", "count": 0}

    sync_count = 0
    modified_prices = []
    
    for item in fetched_items:
        prod_result = await db.execute(
            select(Product).where(
                Product.sku == item["sku"], 
                Product.tenant_id == current_user.tenant_id
            )
        )
        product = prod_result.scalars().first()

        if not product:
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
            if product.price != float(item["price"]):
                product.price = float(item["price"])
                db.add(product)
                await db.commit()
                modified_prices.append((item["sku"], product.price))

        inv_result = await db.execute(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.marketplace == "trendyol"
            )
        )
        inventory = inv_result.scalars().first()

        if inventory:
            inventory.quantity = item["quantity"]
        else:
            new_inv = Inventory(
                product_id=product.id,
                marketplace="trendyol",
                quantity=item["quantity"]
            )
            db.add(new_inv)
        
        await db.commit()
        sync_count += 1

    if modified_prices:
        background_tasks.add_task(push_price_updates_to_others, current_user.tenant_id, "trendyol", modified_prices)

    return {"message": "Trendyol ürünleri başarıyla senkronize edildi", "count": sync_count}


@router.post("/sync/trendyol/orders")
async def sync_trendyol_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "trendyol",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.api_secret or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Trendyol entegrasyonu bulunamadı.")

    from services.marketplace import TrendyolAdapter
    adapter = TrendyolAdapter(supplier_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret))
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
                marketplace="trendyol",
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
        "message": "Trendyol Siparişleri başarıyla çekildi", 
        "order_count": order_sync_count
    }


@router.delete("/clean-mock-orders")
async def clean_mock_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from models.order import Order, OrderItem
    from sqlalchemy import delete
    
    # HB-ORD- ve TY-ORD- ile başlayan, bu tenant'a ait siparişleri bul
    query = select(Order).where(
        Order.tenant_id == current_user.tenant_id,
        Order.order_number.like('HB-ORD-%') | Order.order_number.like('TY-ORD-%')
    )
    result = await db.execute(query)
    mock_orders = result.scalars().all()
    
    deleted_count = 0
    for order in mock_orders:
        await db.execute(delete(OrderItem).where(OrderItem.order_id == order.id))
        await db.execute(delete(Order).where(Order.id == order.id))
        deleted_count += 1
        
    await db.commit()
    return {"message": f"{deleted_count} adet test siparişi başarıyla temizlendi."}


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


@router.post("/sync/amazon")
async def sync_amazon(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Amazon SP-API ürün senkronizasyonu şablonu
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "amazon",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Amazon entegrasyonu bulunamadı (Refresh Token veya Seller ID eksik).")

    return {"message": "Amazon ürün eşitleme entegrasyonu (Simülasyon) başarılı", "count": 0}


@router.post("/sync/amazon/orders")
async def sync_amazon_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "amazon",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Amazon entegrasyonu bulunamadı.")

    from core.config import settings
    from services.marketplace import AmazonAdapter
    adapter = AmazonAdapter(
        refresh_token=str(integration.api_key),
        seller_id=str(integration.store_url),
        region=str(integration.api_secret) or "EU",
        lwa_client_id=settings.AMAZON_LWA_CLIENT_ID,
        lwa_client_secret=settings.AMAZON_LWA_CLIENT_SECRET
    )
    
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
                marketplace="amazon",
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
        "message": "Amazon Siparişleri başarıyla çekildi", 
        "order_count": order_sync_count
    }



@router.post("/sync/pazarama")
async def sync_pazarama(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "pazarama",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Pazarama entegrasyonu bulunamadı.")

    from services.marketplace import PazaramaAdapter
    adapter = PazaramaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret) if integration.api_secret else None)
    
    try:
        fetched_products = await asyncio.to_thread(adapter.fetch_all_products)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    from models.product import Product
    from models.inventory import Inventory
    sync_count = 0
    
    for prod_data in fetched_products:
        prod_result = await db.execute(
            select(Product).where(
                Product.sku == prod_data["sku"],
                Product.tenant_id == current_user.tenant_id
            )
        )
        product = prod_result.scalars().first()
        
        if not product:
            product = Product(
                tenant_id=current_user.tenant_id,
                sku=prod_data["sku"],
                name=prod_data["name"],
                price=prod_data["price"]
            )
            db.add(product)
            await db.commit()
            await db.refresh(product)
        else:
            product.name = prod_data["name"]
            product.price = prod_data["price"]
            db.add(product)
            await db.commit()

        # Envanter (Stok) Güncellemesi
        inv_result = await db.execute(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.marketplace == "pazarama"
            )
        )
        inventory = inv_result.scalars().first()
        
        if inventory:
            inventory.quantity = prod_data["stock"]
        else:
            new_inv = Inventory(
                product_id=product.id,
                marketplace="pazarama",
                quantity=prod_data["stock"]
            )
            db.add(new_inv)
            
        await db.commit()
        sync_count += 1
        
    return {"message": "Pazarama ürün eşitleme başarılı", "count": sync_count}


@router.post("/sync/pazarama/orders")
async def sync_pazarama_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MarketplaceIntegration)
        .where(
            MarketplaceIntegration.tenant_id == current_user.tenant_id,
            MarketplaceIntegration.marketplace_name == "pazarama",
            MarketplaceIntegration.is_active == True
        )
    )
    integration = result.scalars().first()

    if not integration or not integration.api_key or not integration.store_url:
        raise HTTPException(status_code=400, detail="Aktif Pazarama entegrasyonu bulunamadı.")

    from services.marketplace import PazaramaAdapter
    adapter = PazaramaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret) if integration.api_secret else None)
    
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
        if ord_data.get("order_date"):
            try:
                parsed_date = parser.parse(ord_data["order_date"])
            except:
                pass

        if not existing_order:
            new_order = Order(
                tenant_id=current_user.tenant_id,
                marketplace="pazarama",
                order_number=ord_data["order_number"],
                customer_name=ord_data["customer_name"],
                total_price=ord_data["total_price"],
                status=ord_data["status"],
                order_date=parsed_date
            )
            db.add(new_order)
            await db.commit()
            await db.refresh(new_order)
            
            for item in ord_data.get("items", []):
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
        "message": "Pazarama Siparişleri başarıyla çekildi", 
        "order_count": order_sync_count
    }

@router.post("/transfer")
async def transfer_product(
    data: ProductTransferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from services.marketplace import N11Adapter, PazaramaAdapter
    
    # 1. Kaynak ve Hedef entegrasyonlarını bul
    result = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.tenant_id == current_user.tenant_id))
    integrations = result.scalars().all()
    
    source_int = next((i for i in integrations if i.marketplace_name == data.source_marketplace and i.is_active), None)
    target_int = next((i for i in integrations if i.marketplace_name == data.target_marketplace and i.is_active), None)
    
    if not source_int:
        raise HTTPException(status_code=400, detail=f"Kaynak pazaryeri ({data.source_marketplace}) aktif değil veya bulunamadı.")
    if not target_int:
        raise HTTPException(status_code=400, detail=f"Hedef pazaryeri ({data.target_marketplace}) aktif değil veya bulunamadı.")
        
    try:
        # 2. Kaynak platformdan detayları çek
        if data.source_marketplace == "n11":
            source_adapter = N11Adapter(api_key=str(source_int.api_key), api_secret=str(source_int.api_secret))
            product_details = source_adapter.get_product_details(data.sku)
        else:
            raise HTTPException(status_code=400, detail="Desteklenmeyen kaynak pazaryeri")
            
        # 3. Hedef platforma yükle
        if data.target_marketplace == "pazarama":
            target_adapter = PazaramaAdapter(merchant_id=str(target_int.store_url), api_key=str(target_int.api_key), api_secret=str(target_int.api_secret))
            transfer_result = target_adapter.create_product(
                product_data=product_details,
                target_category_id=data.target_category_id,
                target_brand_id=data.target_brand_id,
                vat_rate=data.vat_rate
            )
            
            # Ürünün Pazarama metadata'sını kaydet
            from models.product import Product
            import json
            prod_result = await db.execute(select(Product).where(Product.sku == data.sku, Product.tenant_id == current_user.tenant_id))
            db_product = prod_result.scalars().first()
            if db_product:
                db_product.pazarama_category_id = str(data.target_category_id)
                db_product.pazarama_brand_id = str(data.target_brand_id)
                db_product.images_json = json.dumps(product_details.get("images", []))
                db.add(db_product)
                await db.commit()
                
            return {"message": "Ürün başarıyla aktarıldı", "details": transfer_result}
        else:
            raise HTTPException(status_code=400, detail="Desteklenmeyen hedef pazaryeri")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aktarım başarısız: {str(e)}")

@router.get("/bruteforce-pazarama")
async def bruteforce_pazarama(db: AsyncSession = Depends(get_db)):
    import httpx
    from services.marketplace import PazaramaAdapter
    
    result = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "pazarama", MarketplaceIntegration.is_active == True))
    integration = result.scalars().first()
    if not integration:
        return {"error": "Pazarama entegrasyonu bulunamadı."}
        
    adapter = PazaramaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret))
    try:
        adapter._get_token()
    except Exception as e:
        return {"error": f"Token alınamadı: {str(e)}"}
        
    headers = {
        "Authorization": f"Bearer {adapter.token}",
        "Accept": "application/json"
    }
    
    endpoints = [
        "/Category", "/category", "/categories", "/Categories",
        "/api/Category", "/api/category", "/api/Categories", "/api/categories",
        "/Category/getCategoryTree", "/Category/GetCategoryTree", 
        "/Category/GetCategories", "/Category/getCategories",
        "/category/category-tree", "/category/categoryTree",
        "/api/v1/Category", "/api/v1/category",
        "/Category/getAll", "/category/getAll",
        "/product/category", "/product/categories",
        "/Category/getCategoryWithAttributes", "/category/getCategoryWithAttributes",
        "/Category/get-categories"
    ]
    
    results = {}
    async with httpx.AsyncClient() as client:
        for ep in endpoints:
            try:
                resp = await client.get(f"https://isortagimapi.pazarama.com{ep}", headers=headers, timeout=10.0)
                results[ep] = resp.status_code
                if resp.status_code == 200:
                    results["SUCCESS_URL"] = ep
                    results["SAMPLE_DATA"] = resp.text[:200]
                    break
            except Exception as e:
                results[ep] = f"Error: {str(e)}"
                
    return results

from pydantic import BaseModel
class BulkTransferRequest(BaseModel):
    source_marketplace: str
    target_marketplace: str

@router.post("/bulk-transfer")
async def bulk_transfer_products(
    data: BulkTransferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import difflib
    from services.marketplace import N11Adapter, PazaramaAdapter, ShopifyAdapter
    
    # 1. Entegrasyonları bul
    result = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.tenant_id == current_user.tenant_id))
    integrations = result.scalars().all()
    
    source_int = next((i for i in integrations if i.marketplace_name == data.source_marketplace and i.is_active), None)
    target_int = next((i for i in integrations if i.marketplace_name == data.target_marketplace and i.is_active), None)
    
    if not source_int:
        raise HTTPException(status_code=400, detail=f"Kaynak pazaryeri ({data.source_marketplace}) bulunamadı.")
    if not target_int:
        raise HTTPException(status_code=400, detail=f"Hedef pazaryeri ({data.target_marketplace}) bulunamadı.")
        
    try:
        # 2. Kaynak ürünleri çek
        source_products = []
        source_adapter = None
        if data.source_marketplace == "n11":
            source_adapter = N11Adapter(api_key=str(source_int.api_key), api_secret=str(source_int.api_secret))
            source_products = await asyncio.to_thread(source_adapter.fetch_all_products)
        elif data.source_marketplace == "shopify":
            source_adapter = ShopifyAdapter(api_key=str(source_int.api_key), store_url=str(source_int.store_url))
            source_products = await asyncio.to_thread(source_adapter.fetch_all_products)
        else:
            raise HTTPException(status_code=400, detail="Desteklenmeyen kaynak pazaryeri")
            
        if not source_products:
            return {"message": "Kaynak pazaryerinde aktarılacak ürün bulunamadı.", "results": []}

        # 3. Hedef Pazarama ise Kategori ve Markaları RAM'e al
        target_categories = []
        target_brands = []
        target_adapter = None
        
        if data.target_marketplace == "pazarama":
            target_adapter = PazaramaAdapter(merchant_id=str(target_int.store_url), api_key=str(target_int.api_key), api_secret=str(target_int.api_secret))
            
            cat_res = await target_adapter.get_categories()
            if isinstance(cat_res, dict) and cat_res.get("isSuccess"):
                target_categories = cat_res.get("data", [])
            elif isinstance(cat_res, list):
                target_categories = cat_res
            elif isinstance(cat_res, dict) and "data" in cat_res:
                target_categories = cat_res["data"]
                
            brand_res = await target_adapter.get_brands()
            if isinstance(brand_res, dict) and brand_res.get("isSuccess"):
                target_brands = brand_res.get("data", [])
            elif isinstance(brand_res, list):
                target_brands = brand_res
            elif isinstance(brand_res, dict) and "data" in brand_res:
                target_brands = brand_res["data"]
        else:
            raise HTTPException(status_code=400, detail="Toplu aktarım şimdilik sadece Pazarama hedefine desteklenmektedir.")
            
        cat_names = [(c.get("name") or c.get("displayName") or "").lower() for c in target_categories if isinstance(c, dict)]
        brand_names = [(b.get("name") or b.get("displayName") or "").lower() for b in target_brands if isinstance(b, dict)]
        
        transfer_results = []
        success_count = 0
        
        # 4. Aktarım Döngüsü
        for sp in source_products:
            sku = sp.get("sku")
            if not sku:
                continue
                
            try:
                # Gerçek ürün detayını kaynak adaptörden çek
                details = await asyncio.to_thread(source_adapter.get_product_details, sku)
                source_cat = details.get("category_name", "")
                source_brand = details.get("brand_name", "")
                
                # Kategori eşleştirme (Fuzzy Match)
                target_cat_id = None
                if source_cat:
                    matches = difflib.get_close_matches(source_cat.lower(), cat_names, n=1, cutoff=0.5)
                    if matches:
                        match_name = matches[0]
                        # ID'yi bul
                        target_cat_id = next((c.get("id") for c in target_categories if isinstance(c, dict) and (c.get("name") or c.get("displayName") or "").lower() == match_name), None)
                
                # Marka eşleştirme
                target_brand_id = None
                if source_brand:
                    b_matches = difflib.get_close_matches(source_brand.lower(), brand_names, n=1, cutoff=0.5)
                    if b_matches:
                        b_match = b_matches[0]
                        target_brand_id = next((b.get("id") for b in target_brands if isinstance(b, dict) and (b.get("name") or b.get("displayName") or "").lower() == b_match), None)
                        
                # Eğer bulunamadıysa Pazarama için varsayılan bir ID atamayı deneyebiliriz, şimdilik hata verdiriyoruz.
                if not target_cat_id or not target_brand_id:
                    transfer_results.append({
                        "sku": sku, 
                        "name": details.get("name"), 
                        "status": "error", 
                        "reason": f"Kategori veya Marka eşleşmedi. (Kaynak Cat: {source_cat}, Brand: {source_brand})"
                    })
                    continue
                    
                # Hedefe gönder
                res = await asyncio.to_thread(target_adapter.create_product, details, target_cat_id, target_brand_id, 20)
                
                if res.get("isSuccess"):
                    success_count += 1
                    transfer_results.append({"sku": sku, "name": details.get("name"), "status": "success", "reason": "Başarılı"})
                else:
                    transfer_results.append({"sku": sku, "name": details.get("name"), "status": "error", "reason": str(res.get("messages", "Bilinmeyen hata"))})
                    
            except Exception as e:
                transfer_results.append({"sku": sku, "name": sp.get("name"), "status": "error", "reason": str(e)})
                
        return {
            "message": f"{len(source_products)} üründen {success_count} tanesi başarıyla aktarıldı.",
            "results": transfer_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pazarama/categories")
async def get_pazarama_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from services.marketplace import PazaramaAdapter
    result = await db.execute(select(MarketplaceIntegration).where(
        MarketplaceIntegration.tenant_id == current_user.tenant_id,
        MarketplaceIntegration.marketplace_name == "pazarama",
        MarketplaceIntegration.is_active == True
    ))
    integration = result.scalars().first()
    if not integration:
        raise HTTPException(status_code=400, detail="Pazarama entegrasyonu bulunamadı veya aktif değil.")
        
    try:
        adapter = PazaramaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret) if integration.api_secret else None)
        cats = await adapter.get_categories()
        return cats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pazarama/brands")
async def get_pazarama_brands(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from services.marketplace import PazaramaAdapter
    result = await db.execute(select(MarketplaceIntegration).where(
        MarketplaceIntegration.tenant_id == current_user.tenant_id,
        MarketplaceIntegration.marketplace_name == "pazarama",
        MarketplaceIntegration.is_active == True
    ))
    integration = result.scalars().first()
    if not integration:
        raise HTTPException(status_code=400, detail="Pazarama entegrasyonu bulunamadı veya aktif değil.")
        
    try:
        adapter = PazaramaAdapter(merchant_id=str(integration.store_url), api_key=str(integration.api_key), api_secret=str(integration.api_secret) if integration.api_secret else None)
        brands = await adapter.get_brands()
        return brands
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
