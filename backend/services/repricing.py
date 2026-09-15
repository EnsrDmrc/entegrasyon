import asyncio
import datetime
import logging
from typing import List

logger = logging.getLogger("uvicorn.error")
from sqlalchemy.future import select
from core.database import AsyncSessionLocal
from models.product import Product
from models.inventory import Inventory
from models.tenant import Tenant
from models.integration import MarketplaceIntegration
from services.n11_scraper import N11Scraper
from services.marketplace import N11Adapter

async def run_n11_repricing():
    """
    Günde 1 kez çalışacak N11 Otomatik Fiyatlandırma (Repricing) Motoru.
    Kural:
    - Stokta olan ve N11 URL'si girilmiş ürünleri tarar.
    - Sadece N11 entegrasyonu aktif olan satıcılar için çalışır.
    - Bizim ürünümüz en ucuz ise, 2. sıradaki rakibin fiyatından 10 TL ucuz olacak şekilde günceller.
    - Fark zaten 10 TL ve altındaysa dokunmaz.
    - En ucuz biz değilsek (veyahut tek satıcıysak) dokunmaz.
    - N11 destekli indirim varsa (scraper'dan gelen discount_rate), hesaplanan hedef fiyata bu indirimi tersine uygulayarak ana fiyatı bulur.
    """
    logger.info("[Repricing] N11 Otomatik Fiyatlandırma motoru başlatıldı...")
    scraper = N11Scraper()
    
    async with AsyncSessionLocal() as db:
        # N11 Entegrasyonu aktif olan tenant'ları bul
        n11_integrations_res = await db.execute(
            select(MarketplaceIntegration).where(
                MarketplaceIntegration.marketplace_name == "n11",
                MarketplaceIntegration.is_active == True
            )
        )
        n11_integrations = n11_integrations_res.scalars().all()
        
        if not n11_integrations:
            logger.info("[Repricing] Aktif N11 entegrasyonu bulunamadı.")
            return
            
        for integration in n11_integrations:
            tenant_res = await db.execute(select(Tenant).where(Tenant.id == integration.tenant_id))
            tenant = tenant_res.scalars().first()
            if not tenant: continue
            
            tenant_name = tenant.name.lower().strip()
            
            # Bu tenant'ın n11_url'si olan ürünlerini bul
            products_res = await db.execute(
                select(Product).where(
                    Product.tenant_id == tenant.id,
                    Product.n11_url != None
                )
            )
            products = products_res.scalars().all()
            
            # N11 Adapter'ı hazırla (Fiyat güncellemek için)
            adapter = N11Adapter(api_key=integration.api_key, api_secret=integration.api_secret)
            
            for product in products:
                # Stok kontrolü
                inv_res = await db.execute(
                    select(Inventory).where(
                        Inventory.product_id == product.id,
                        Inventory.marketplace == "n11"
                    )
                )
                inventory = inv_res.scalars().first()
                if not inventory or inventory.quantity <= 0:
                    logger.info(f"[Repricing] {product.sku} stokta yok, atlanıyor.")
                    continue
                    
                # Rakipleri çek
                logger.info(f"[Repricing] {product.sku} için N11 URL: {product.n11_url}")
                competitors = scraper.get_competitors(product.n11_url)
                if not competitors:
                    logger.info(f"[Repricing] {product.sku} için rakip bulunamadı veya sayfa okunamadı.")
                    continue
                    
                if len(competitors) == 1:
                    logger.info(f"[Repricing] {product.sku} için sadece biz varız (tek satıcı), fiyata dokunulmuyor.")
                    continue
                    
                # Rakipler zaten küçükten büyüğe sıralı
                cheapest = competitors[0]
                second_cheapest = competitors[1]
                
                # En ucuz biz miyiz kontrolü
                is_cheapest_us = False
                cheapest_seller_name = cheapest["seller_name"].lower().strip()
                tenant_name_clean = tenant_name.replace(" ", "")
                cheapest_seller_name_clean = cheapest_seller_name.replace(" ", "")
                
                # Tenant name ile satıcı adı eşleşiyor mu?
                if tenant_name_clean in cheapest_seller_name_clean or cheapest_seller_name_clean in tenant_name_clean:
                    is_cheapest_us = True
                
                # İsme göre bulamazsak, fiyata göre tahmin etmeye çalış (Eğer N11 API'ye yansıyan fiyatımız buysa)
                # İndirimsiz halini DB'deki fiyatımızla karşılaştırabiliriz, ama isme güvenmek en doğrusu.
                
                from datetime import datetime, timezone
                
                # Bizim kendi mağazamızın anlık bilgilerini scraper sonucundan bul (Sepet fiyatımızı göstermek için)
                our_product_info = None
                for c in competitors:
                    c_name_clean = c["seller_name"].lower().strip().replace(" ", "")
                    if tenant_name_clean in c_name_clean or c_name_clean in tenant_name_clean:
                        our_product_info = c
                        break
                        
                our_current_cart_price = our_product_info["price"] if our_product_info else float(product.price)
                
                if not is_cheapest_us:
                    logger.info(f"[Repricing] {product.sku} için en ucuz biz değiliz (En ucuz: {cheapest_seller_name}). Dokunulmuyor.")
                    product.is_expensive = 1
                    product.our_cart_price = our_current_cart_price
                    product.cheapest_competitor_price = cheapest["price"]
                    product.cheapest_competitor_name = cheapest["seller_name"]
                    product.last_repricing_check = datetime.now(timezone.utc)
                    db.add(product)
                    await db.commit()
                    continue
                    
                # En ucuz biz isek, is_expensive durumunu temizle
                product.is_expensive = 0
                product.our_cart_price = our_current_cart_price
                product.cheapest_competitor_price = cheapest["price"]
                product.cheapest_competitor_name = cheapest["seller_name"]
                product.last_repricing_check = datetime.now(timezone.utc)
                
                # En ucuz biz isek, kâr maksimizasyonu yap
                price_diff = second_cheapest["price"] - cheapest["price"]
                
                if price_diff <= 10.0:
                    logger.info(f"[Repricing] {product.sku} için en ucuz biziz ancak 2. sıradaki ile fark {price_diff} TL (<=10). Dokunulmuyor.")
                    continue
                    
                # Yeni hedef fiyat (Müşterinin göreceği nihai sepet fiyatı)
                target_final_price = second_cheapest["price"] - 10.0
                
                # N11 platform indirimini DB üzerinden tahmin etmek Fiyat SARMALI (Price Spiral) yaratır.
                # Bu yüzden scraper'ın çektiği 'platform_discount' verisini doğrudan kullanıyoruz.
                actual_discount_rate = cheapest.get("platform_discount", 0.0)
                
                if actual_discount_rate > 0:
                    multiplier = 1 - actual_discount_rate
                    new_base_price = target_final_price / multiplier
                    logger.info(f"[Repricing] {product.sku} İndirim Oranı: %{actual_discount_rate*100:.2f}. Hedef Sepet: {target_final_price} TL -> API'ye gönderilecek İndirimsiz Fiyat: {new_base_price:.2f} TL")
                else:
                    new_base_price = target_final_price
                    logger.info(f"[Repricing] {product.sku} için yeni fiyat hesaplandı: {new_base_price:.2f} TL")
                    
                # Fiyatı yuvarla (2 hane)
                new_base_price = round(new_base_price, 2)
                
                # N11'e yolla
                success = adapter.update_product(sku=product.sku, new_price=new_base_price)
                if success:
                    # DB'yi de güncelle
                    product.price = new_base_price
                    db.add(product)
                    logger.info(f"[Repricing] {product.sku} başarıyla güncellendi!")
                else:
                    logger.info(f"[Repricing] {product.sku} N11 API güncellenirken hata oluştu.")
                    
        await db.commit()
    logger.info("[Repricing] N11 Otomatik Fiyatlandırma tamamlandı.")

async def repricing_loop():
    """
    Arka planda sürekli çalışarak her gece saat 03:00'da repricing görevini tetikler.
    """
    logger.info("[Repricing] Döngü başlatıldı. Görev her gece 03:00'da çalışacak.")
    while True:
        now = datetime.datetime.now()
        target = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)
            
        wait_seconds = (target - now).total_seconds()
        logger.info(f"[Repricing] Bir sonraki taramaya {int(wait_seconds)} saniye var ({target}).")
        
        # O saat gelene kadar bekle
        await asyncio.sleep(wait_seconds)
        
        try:
            await run_n11_repricing()
        except Exception as e:
            print(f"[Repricing] HATA: {e}")
