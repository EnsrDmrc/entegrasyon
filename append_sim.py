
with open('backend/api/routes/integrations.py', 'a', encoding='utf-8') as f:
    f.write('''
@router.post("/simulate/pazarama/order")
async def simulate_pazarama_order(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Bu endpoint gerçek dışı sahte bir Pazarama siparişi
    oluşturarak sistemi test etmemizi sağlar. 
    """
    try:
        from models.tenant import MarketplaceIntegration
        from models.product import Product
        from models.order import Order, OrderItem
        import uuid
        
        # 1. Pazarama entegrasyonu olan herhangi bir tenant bul
        result = await db.execute(
            select(MarketplaceIntegration).where(
                MarketplaceIntegration.marketplace_name == "pazarama"
            )
        )
        integration = result.scalars().first()
        if not integration:
            raise HTTPException(status_code=400, detail="Pazarama entegrasyonu bulunamadı.")
            
        # 2. Test için bir ürün bul
        prod_res = await db.execute(select(Product).where(Product.tenant_id == integration.tenant_id))
        product = prod_res.scalars().first()
        if not product:
            raise HTTPException(status_code=400, detail="Test için veritabanında ürün bulunamadı.")
            
        # 3. Sahte Sipariş Oluştur
        import random
        fake_order_no = str(random.randint(100000000, 999999999))
        
        new_order = Order(
            tenant_id=integration.tenant_id,
            marketplace="pazarama",
            order_number=fake_order_no,
            customer_name="Pazarama Test Müşterisi",
            total_price=float(product.price),
            status="Yeni Sipariş"
        )
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)
        
        # 4. Sahte Sipariş Kalemi Oluştur
        new_item = OrderItem(
            order_id=new_order.id,
            product_sku=product.sku,
            product_name=product.name,
            quantity=1,
            price=float(product.price)
        )
        db.add(new_item)
        
        # 5. Stoğu düş!
        product.stock_quantity = max(0, product.stock_quantity - 1)
        db.add(product)
        await db.commit()
        
        # 6. Diğer pazaryerlerine (Shopify, N11, HB) bildir
        modified_stocks = [(product.sku, product.stock_quantity)]
        background_tasks.add_task(push_stock_updates_to_others, integration.tenant_id, "pazarama", modified_stocks)
        
        return {
            "message": "Sahte Pazarama Siparişi simüle edildi ve stok düşüldü! Diğer kanallara (Shopify, N11, HB) aktarılıyor...",
            "order_number": fake_order_no,
            "deducted_sku": product.sku,
            "remaining_stock": product.stock_quantity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
''')
