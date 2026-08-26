import os
code = """
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
"""

with open("backend/api/routes/integrations.py", "a", encoding="utf-8") as f:
    f.write(code)
print("Appended successfully")
