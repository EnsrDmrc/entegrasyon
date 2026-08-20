import asyncio
import httpx
from sqlalchemy.future import select
from core.database import AsyncSessionLocal
from models.integration import MarketplaceIntegration
from models.product import Product

async def main():
    async with AsyncSessionLocal() as db:
        # Get active shopify integration
        int_result = await db.execute(
            select(MarketplaceIntegration)
            .where(MarketplaceIntegration.marketplace_name == "shopify", MarketplaceIntegration.is_active == True)
        )
        integration = int_result.scalars().first()
        if not integration:
            print("No active Shopify integration found.")
            return

        api_key = str(integration.api_key)
        store_url = str(integration.store_url).replace("https://", "").replace("http://", "").strip("/")
        base_url = f"https://{store_url}/admin/api/2024-01"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": api_key
        }

        print(f"Testing with store: {store_url}")
        
        with httpx.Client() as client:
            scope_res = client.get(f"https://{store_url}/admin/oauth/access_scopes.json", headers=headers)
            print(f"Token Scopes: {scope_res.json()}")

        # Get a product to test
        prod_result = await db.execute(select(Product).where(Product.tenant_id == integration.tenant_id))
        products = prod_result.scalars().all()
        
        test_sku = None
        for p in products:
            if not p.sku.startswith("TEST-"):
                test_sku = p.sku
                break
                
        if not test_sku:
            print("No valid product found to test.")
            return
            
        print(f"Testing with SKU: {test_sku}")

        # Find variant_id and inventory_item_id
        variant_id = None
        inventory_item_id = None
        
        with httpx.Client() as client:
            if test_sku.startswith("SHOP-"):
                var_id = test_sku.replace("SHOP-", "")
                resp = client.get(f"{base_url}/variants/{var_id}.json", headers=headers)
                if resp.status_code == 200:
                    var_data = resp.json().get("variant", {})
                    variant_id = var_data.get("id")
                    inventory_item_id = var_data.get("inventory_item_id")
            else:
                url = f"{base_url}/products.json?limit=250"
                found = False
                while url and not found:
                    resp = client.get(url, headers=headers)
                    if resp.status_code != 200:
                        break
                    data = resp.json()
                    for prod in data.get("products", []):
                        for var in prod.get("variants", []):
                            if var.get("sku") == test_sku:
                                variant_id = var.get("id")
                                inventory_item_id = var.get("inventory_item_id")
                                found = True
                                break
                        if found: break
                    if "next" in resp.links:
                        url = resp.links["next"]["url"]
                    else:
                        url = None

            print(f"Variant ID: {variant_id}, Inventory Item ID: {inventory_item_id}")

            if variant_id and inventory_item_id:
                loc_res = client.get(f"{base_url}/locations.json", headers=headers)
                print(f"Locations Status: {loc_res.status_code}")
                if loc_res.status_code == 200:
                    locations = loc_res.json().get("locations", [])
                    print(f"Locations: {[l['id'] for l in locations]}")
                    if locations:
                        location_id = locations[0]["id"]
                        inv_payload = {
                            "location_id": location_id,
                            "inventory_item_id": inventory_item_id,
                            "available": 5  # Test with 5
                        }
                        print(f"Sending payload: {inv_payload}")
                        inv_res = client.post(f"{base_url}/inventory_levels/set.json", headers=headers, json=inv_payload)
                        print(f"Inventory Update Status: {inv_res.status_code}")
                        print(f"Inventory Update Response: {inv_res.text}")

if __name__ == "__main__":
    asyncio.run(main())
