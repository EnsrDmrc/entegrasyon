import re

def patch_file():
    with open('api/routes/integrations.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_code = '''    from models.product import Product
    sync_count = 0
    for prod_data in fetched_products:
        prod_result = await db.execute(
            select(Product).where(
                Product.sku == prod_data["sku"],
                Product.tenant_id == current_user.tenant_id
            )
        )
        existing_product = prod_result.scalars().first()
        
        if existing_product:
            existing_product.price = prod_data["price"]
        else:
            new_product = Product(
                tenant_id=current_user.tenant_id,
                sku=prod_data["sku"],
                name=prod_data["name"],
                price=prod_data["price"]
            )
            db.add(new_product)
        sync_count += 1
    
    await db.commit()
    return {"message": "Pazarama ürün eşitleme başarılı", "count": sync_count}'''

    new_code = '''    from models.product import Product
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
        
    return {"message": "Pazarama ürün eşitleme başarılı", "count": sync_count}'''

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open('api/routes/integrations.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Patched successfully")
    else:
        print("Could not find exact old code!")

patch_file()
