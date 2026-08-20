import asyncio
import random
from sqlalchemy.future import select
from models.tenant import Tenant
from models.product import Product
from models.inventory import Inventory
from models.order import Order, OrderItem
from models.integration import MarketplaceIntegration
from core.database import AsyncSessionLocal
from datetime import datetime
from services.marketplace import ShopifyAdapter

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant))
        tenants = result.scalars().all()
        if not tenants:
            print("No tenant found.")
            return

        for tenant in tenants:
            print(f"Creating order for Tenant: {tenant.name} (ID: {tenant.id})")

            prod_result = await db.execute(select(Product).where(Product.tenant_id == tenant.id))
            products = prod_result.scalars().all()
            
            if not products:
                print(f"No products found for tenant {tenant.name}. Skipping...")
                continue
                
            random_product = random.choice(products)
            
            inv_result = await db.execute(select(Inventory).where(Inventory.product_id == random_product.id))
            inventories = inv_result.scalars().all()
            
            qty_ordered = 1
            new_stock = None
            if inventories:
                if inventories[0].quantity >= qty_ordered:
                    inventories[0].quantity -= qty_ordered
                else:
                    inventories[0].quantity = 0
                new_stock = inventories[0].quantity
                db.add(inventories[0])
            
            new_order = Order(
                tenant_id=tenant.id,
                marketplace="shopify_test",
                order_number=f"TEST-{random.randint(1000, 9999)}-{tenant.id}",
                customer_name="Rastgele Müşteri",
                total_price=random_product.price * qty_ordered,
                status="paid",
                order_date=datetime.now()
            )
            db.add(new_order)
            await db.commit()
            await db.refresh(new_order)

            new_item = OrderItem(
                order_id=new_order.id,
                product_sku=random_product.sku,
                product_name=random_product.name,
                quantity=qty_ordered,
                price=random_product.price
            )
            db.add(new_item)
            await db.commit()
            
            # --- SHOPIFY'A STOK DÜŞÜŞÜNÜ BİLDİR (Burası eksikti) ---
            if new_stock is not None:
                int_result = await db.execute(
                    select(MarketplaceIntegration)
                    .where(MarketplaceIntegration.tenant_id == tenant.id, MarketplaceIntegration.marketplace_name == "shopify")
                )
                integration = int_result.scalars().first()
                if integration and integration.is_active and integration.api_key:
                    print(f"Syncing stock reduction to Shopify for SKU: {random_product.sku}, new stock: {new_stock}")
                    adapter = ShopifyAdapter(api_key=str(integration.api_key), store_url=str(integration.store_url))
                    success = adapter.update_product(sku=random_product.sku, new_stock=new_stock)
                    if success:
                        print("Successfully synced to Shopify!")
                    else:
                        print("Failed to sync to Shopify.")
            
        print("Test orders created successfully for all tenants!")

if __name__ == "__main__":
    asyncio.run(main())
