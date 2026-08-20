from core.celery_app import celery_app
import time

@celery_app.task
def sync_inventory(product_id: int, new_quantity: int, origin_marketplace: str):
    """
    Bu task, bir pazaryerinden (örneğin Shopify) gelen sipariş sonucu 
    düşen stoğu, diğer pazaryerlerine (örneğin n11) iletmek için arka planda çalışır.
    """
    print(f"[SYNC] Senkronizasyon başlatıldı...")
    print(f"Ürün ID: {product_id} | Yeni Stok: {new_quantity} | Kaynak: {origin_marketplace}")
    
    # Gerçek senaryoda burada ilgili pazar yeri API'lerine (n11, Trendyol vb.) istek atılır.
    # Örn: n11_api.update_stock(product_id, new_quantity)
    
    time.sleep(2) # Simülasyon
    
    print(f"[SYNC] Bütün pazaryerleri güncellendi (Ürün ID: {product_id}).")
    return True
