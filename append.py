
with open('backend/api/routes/integrations.py', 'a', encoding='utf-8') as f:
    f.write('''
@router.post("/sync/pazarama/orders")
async def sync_pazarama_orders(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
    from models.product import Product
    from dateutil import parser
    
    order_sync_count = 0
    modified_stocks = []
    
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
                parsed_date = parser.parse(ord_data["order_date"], dayfirst=True)
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
            
            for item in ord_data["items"]:
                new_item = OrderItem(
                    order_id=new_order.id,
                    product_sku=item["product_sku"],
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
                db.add(new_item)
                
                # Stoktan düş!
                prod_res = await db.execute(select(Product).where(Product.sku == item["product_sku"], Product.tenant_id == current_user.tenant_id))
                product = prod_res.scalars().first()
                if product:
                    product.stock_quantity = max(0, product.stock_quantity - item["quantity"])
                    db.add(product)
                    modified_stocks.append((product.sku, product.stock_quantity))
                    
            await db.commit()
            order_sync_count += 1
        else:
            if existing_order.status != ord_data["status"]:
                existing_order.status = ord_data["status"]
                db.add(existing_order)
                await db.commit()
                order_sync_count += 1

    if modified_stocks:
        background_tasks.add_task(push_stock_updates_to_others, current_user.tenant_id, "pazarama", modified_stocks)

    return {
        "message": "Pazarama siparişleri başarıyla çekildi ve stoklar düşüldü!", 
        "order_count": order_sync_count
    }
''')
