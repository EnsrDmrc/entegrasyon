import asyncio
import json
import logging
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List

from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
from sqlalchemy.future import select

logger = logging.getLogger("uvicorn.error")
from core.database import AsyncSessionLocal
from models.product import Product
from models.inventory import Inventory
from models.tenant import Tenant
from models.integration import MarketplaceIntegration
from services.n11_scraper import N11Scraper
from services.marketplace import N11Adapter

async def run_n11_repricing():
    """
    N11 Veri Toplama Motoru.
    Kural:
    - Stokta olan ve N11 URL'si girilmiş ürünleri tarar.
    - Tüm rakipleri, fiyatlarını ve stoklarını çeker.
    - Veritabanına competitors_json olarak kaydeder.
    - Eskisi gibi otomatik fiyat değiştirmez, sadece analiz yapar.
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
            
            # Bu tenant'ın tüm ürünlerini bul (URL'si olmayanları da)
            products_res = await db.execute(
                select(Product).where(
                    Product.tenant_id == tenant.id
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
                    
                # N11 URL'si yoksa otomatik bul
                if not product.n11_url and product.sku:
                    logger.info(f"[Repricing] {product.sku} için N11 URL'si yok. Otomatik aranıyor...")
                    import urllib.parse
                    import json
                    from bs4 import BeautifulSoup
                    from curl_cffi import requests as curl_requests
                    
                    search_query = product.sku
                    encoded_q = urllib.parse.quote(search_query)
                    search_url = f"https://www.n11.com/arama?q={encoded_q}"
                    
                    try:
                        resp = curl_requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, impersonate="chrome110", timeout=10.0)
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, 'lxml')
                            for script in soup.find_all('script'):
                                if script.string and 'window.model = ' in script.string:
                                    raw = script.string.strip()
                                    start = raw.find('window.model = ') + len('window.model = ')
                                    jstr = raw[start:]
                                    if jstr.endswith(';'): jstr = jstr[:-1]
                                    data = json.loads(jstr)
                                    results = data.get('searchResults', [])
                                    if results and len(results) > 0:
                                        first_item = results[0]
                                        found_url = first_item.get('url') or first_item.get('productUrl')
                                        if found_url:
                                            if found_url.startswith('/'):
                                                found_url = 'https://www.n11.com' + found_url
                                            product.n11_url = found_url
                                            db.add(product)
                                            await db.commit()
                                            logger.info(f"[Repricing] {product.sku} için link bulundu: {found_url}")
                                            break
                    except Exception as e:
                        logger.error(f"[Repricing] {product.sku} aranırken hata: {e}")
                
                if not product.n11_url:
                    logger.info(f"[Repricing] {product.sku} için N11 URL bulunamadı, atlanıyor.")
                    continue
                    
                # Rakipleri çek
                logger.info(f"[Repricing] {product.sku} için N11 URL: {product.n11_url}")
                competitors = scraper.get_competitors(product.n11_url)
                import json
                
                if not competitors:
                    logger.info(f"[Repricing] {product.sku} için rakip bulunamadı veya sayfa okunamadı.")
                    product.competitors_json = json.dumps([], ensure_ascii=False)
                    product.last_repricing_check = datetime.now(timezone.utc)
                    product.cheapest_competitor_price = 0
                    product.cheapest_competitor_name = ""
                    db.add(product)
                    await db.commit()
                    continue
                    
                if len(competitors) == 1:
                    logger.info(f"[Repricing] {product.sku} için sadece biz varız (tek satıcı).")
                    product.competitors_json = json.dumps(competitors, ensure_ascii=False)
                    product.last_repricing_check = datetime.now(timezone.utc)
                    product.cheapest_competitor_price = 0
                    product.cheapest_competitor_name = ""
                    product.is_expensive = 0
                    our_current_cart_price = competitors[0]["price"]
                    product.our_cart_price = our_current_cart_price
                    db.add(product)
                    await db.commit()
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
                
                # Bizim kendi mağazamızın anlık bilgilerini scraper sonucundan bul (Sepet fiyatımızı göstermek için)
                our_product_info = None
                for c in competitors:
                    c_name_clean = c["seller_name"].lower().strip().replace(" ", "")
                    if tenant_name_clean in c_name_clean or c_name_clean in tenant_name_clean:
                        our_product_info = c
                        break
                        
                our_current_cart_price = float(product.price)
                if our_product_info:
                    our_current_cart_price = our_product_info["price"]
                
                product.is_expensive = 1 if not is_cheapest_us else 0
                product.our_cart_price = our_current_cart_price
                
                if is_cheapest_us:
                    product.cheapest_competitor_price = second_cheapest["price"]
                    product.cheapest_competitor_name = second_cheapest["seller_name"]
                else:
                    product.cheapest_competitor_price = cheapest["price"]
                    product.cheapest_competitor_name = cheapest["seller_name"]
                    
                product.competitors_json = json.dumps(competitors, ensure_ascii=False)
                product.last_repricing_check = datetime.now(timezone.utc)
                
                db.add(product)
                    
        await db.commit()
    logger.info("[Repricing] N11 Veri Toplama ve Analiz tamamlandı.")

async def repricing_loop():
    """
    Arka planda sürekli çalışarak her gece saat 03:00'da repricing görevini tetikler.
    """
    logger.info("[Repricing] Döngü başlatıldı. Görev her gece 03:00'da çalışacak.")
    while True:
        now = datetime.now()
        target = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
            
        wait_seconds = (target - now).total_seconds()
        logger.info(f"[Repricing] Bir sonraki taramaya {int(wait_seconds)} saniye var ({target}).")
        
        # O saat gelene kadar bekle
        await asyncio.sleep(wait_seconds)
        
        try:
            await run_n11_repricing()
        except Exception as e:
            print(f"[Repricing] HATA: {e}")
