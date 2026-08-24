import asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from dateutil import parser
from core.database import AsyncSessionLocal
from models.integration import MarketplaceIntegration
from models.order import Order, OrderItem
from models.product import Product
from models.inventory import Inventory
from services.marketplace import N11Adapter, ShopifyAdapter

async def process_tenant_orders(session, tenant_id: int):
    # Entegrasyonları çek
    int_result = await session.execute(
        select(MarketplaceIntegration)
        .where(MarketplaceIntegration.tenant_id == tenant_id, MarketplaceIntegration.is_active == True)
    )
    integrations = int_result.scalars().all()
    
    n11_int = next((i for i in integrations if i.marketplace_name == 'n11'), None)
    shopify_int = next((i for i in integrations if i.marketplace_name == 'shopify'), None)
    hepsiburada_int = next((i for i in integrations if i.marketplace_name == 'hepsiburada'), None)
    
    fetched_orders = []
    n11_adapter = None
    shopify_adapter = None
    hepsiburada_adapter = None
    
    try:
        # Fetch N11 orders
        if n11_int and n11_int.api_key and n11_int.api_secret:
            n11_adapter = N11Adapter(api_key=str(n11_int.api_key), api_secret=str(n11_int.api_secret))
            n11_orders = await asyncio.to_thread(n11_adapter.fetch_orders)
            for o in n11_orders:
                o["marketplace"] = "n11"
            fetched_orders.extend(n11_orders)
    except Exception as e:
        print(f"[Patrol] N11 Order fetch failed for tenant {tenant_id}: {e}")

    try:
        # Fetch Shopify orders
        if shopify_int and shopify_int.api_key and shopify_int.store_url:
            shopify_adapter = ShopifyAdapter(api_key=str(shopify_int.api_key), store_url=str(shopify_int.store_url))
            shop_orders = await asyncio.to_thread(shopify_adapter.fetch_orders)
            for o in shop_orders:
                o["marketplace"] = "shopify"
            fetched_orders.extend(shop_orders)
    except Exception as e:
        print(f"[Patrol] Shopify Order fetch failed for tenant {tenant_id}: {e}")

    try:
        # Fetch Hepsiburada orders
        from services.marketplace import HepsiburadaAdapter
        if hepsiburada_int and hepsiburada_int.api_key and hepsiburada_int.store_url:
            # api_key -> API Şifresi, store_url -> Merchant ID
            hepsiburada_adapter = HepsiburadaAdapter(merchant_id=str(hepsiburada_int.store_url), api_key=str(hepsiburada_int.api_key))
            hb_orders = await asyncio.to_thread(hepsiburada_adapter.fetch_orders)
            for o in hb_orders:
                o["marketplace"] = "hepsiburada"
            fetched_orders.extend(hb_orders)
    except Exception as e:
        print(f"[Patrol] Hepsiburada Order fetch failed for tenant {tenant_id}: {e}")
    
    for ord_data in fetched_orders:
        order_number = ord_data.get("order_number")
        
        # 1. Idempotency Check: Sipariş daha önce çekilmiş mi?
        ord_result = await session.execute(
            select(Order).where(
                Order.order_number == order_number,
                Order.tenant_id == tenant_id
            )
        )
        existing_order = ord_result.scalars().first()
        
        if existing_order:
            # Sipariş zaten var, ancak statüsü değişmiş olabilir (ör: Onaylandı -> Teslim Edildi)
            if existing_order.status != ord_data.get("status"):
                existing_order.status = ord_data.get("status")
                session.add(existing_order)
                await session.commit()
            continue
            
        print(f"[Patrol] Yeni sipariş algılandı! Order No: {order_number}")
        
        # 2. Siparişi veritabanına kaydet
        parsed_date = None
        if ord_data.get("order_date"):
            try:
                parsed_date = parser.parse(ord_data["order_date"], dayfirst=True)
            except:
                pass

        new_order = Order(
            tenant_id=tenant_id,
            marketplace=ord_data.get("marketplace", "unknown"),
            order_number=order_number,
            customer_name=ord_data.get("customer_name"),
            total_price=ord_data.get("total_price"),
            status=ord_data.get("status"),
            order_date=parsed_date
        )
        session.add(new_order)
        await session.commit()
        await session.refresh(new_order)
        
        modified_products = []
        
        # 3. Sipariş kalemlerini ekle ve stokları düşür
        for item in ord_data.get("items", []):
            sku = item.get("product_sku")
            qty_ordered = int(item.get("quantity", 1))
            
            new_item = OrderItem(
                order_id=new_order.id,
                product_sku=sku,
                product_name=item.get("product_name"),
                quantity=qty_ordered,
                price=item.get("price")
            )
            session.add(new_item)
            
            # Stok Düşürme Mantığı
            prod_res = await session.execute(
                select(Product)
                .where(Product.tenant_id == tenant_id, Product.sku == sku)
                .options(selectinload(Product.inventories))
            )
            product = prod_res.scalars().first()
            
            if product and product.inventories:
                new_total_stock = 0
                for inv in product.inventories:
                    current_stock = inv.quantity
                    updated_stock = max(0, current_stock - qty_ordered)
                    inv.quantity = updated_stock
                    session.add(inv)
                    new_total_stock = updated_stock
                
                modified_products.append((sku, new_total_stock))
        
        await session.commit()
        
        # 4. Güncellenen stokları pazar yerlerine PUSH et
        for sku, new_stock in modified_products:
            print(f"[Patrol] SKU {sku} için yeni stok {new_stock} olarak diğer pazaryerlerine itiliyor...")
            
            # Shopify'a it
            if shopify_adapter:
                await asyncio.to_thread(shopify_adapter.update_product, sku, new_stock=new_stock)
                
            # N11'e it
            if n11_adapter:
                await asyncio.to_thread(n11_adapter.update_product, sku, new_stock=new_stock)
                
            # Hepsiburada'ya it
            if hepsiburada_adapter:
                await asyncio.to_thread(hepsiburada_adapter.update_product, sku, new_stock=new_stock)

async def order_patrol_loop():
    print("[Patrol] Sipariş Devriyesi başlatıldı! Her 1 dakikada bir çalışacak.")
    while True:
        try:
            async with AsyncSessionLocal() as session:
                tenant_res = await session.execute(select(MarketplaceIntegration.tenant_id).distinct())
                tenant_ids = [row[0] for row in tenant_res.all()]
                for t_id in tenant_ids:
                    await process_tenant_orders(session, t_id)
        except Exception as e:
            print(f"[Patrol] Devriye sırasında hata: {e}")
        
        # 90 saniye bekle (Kullanıcı isteği)
        await asyncio.sleep(90)
