from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.patrol import order_patrol_loop
    from core.database import AsyncSessionLocal
    from sqlalchemy import text
    
    # Otomatik veritabanı göçü (Sütun eklemeleri)
    async with AsyncSessionLocal() as session:
        # Users tablosu
        try:
            await session.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT TRUE;"))
            await session.execute(text("ALTER TABLE users ADD COLUMN otp_code VARCHAR;"))
            await session.execute(text("ALTER TABLE users ADD COLUMN otp_expires_at TIMESTAMP WITH TIME ZONE;"))
            await session.execute(text("UPDATE users SET is_verified = TRUE WHERE is_verified IS NULL;"))
            await session.commit()
        except Exception as e:
            await session.rollback()
            
        # Products tablosu
        try:
            await session.execute(text("ALTER TABLE products ADD COLUMN pazarama_category_id VARCHAR;"))
            await session.commit()
        except Exception as e:
            await session.rollback()

        try:
            await session.execute(text("ALTER TABLE products ADD COLUMN pazarama_brand_id VARCHAR;"))
            await session.commit()
        except Exception as e:
            await session.rollback()

        try:
            await session.execute(text("ALTER TABLE products ADD COLUMN images_json VARCHAR;"))
            await session.commit()
        except Exception as e:
            await session.rollback()

        try:
            await session.execute(text("ALTER TABLE products ADD COLUMN is_expensive INTEGER DEFAULT 0;"))
            await session.commit()
        except Exception:
            await session.rollback()
            
        try:
            await session.execute(text("ALTER TABLE products ADD COLUMN our_cart_price FLOAT;"))
            await session.commit()
        except Exception:
            await session.rollback()
            
        try:
            await session.execute(text("ALTER TABLE products ADD COLUMN cheapest_competitor_price FLOAT;"))
            await session.commit()
        except Exception:
            await session.rollback()
            
        try:
            await session.execute(text("ALTER TABLE products ADD COLUMN cheapest_competitor_name VARCHAR;"))
            await session.commit()
        except Exception:
            await session.rollback()
            
        try:
            await session.execute(text("ALTER TABLE products ADD COLUMN last_repricing_check TIMESTAMP WITH TIME ZONE;"))
            await session.commit()
        except Exception:
            await session.rollback()
            
        try:
            await session.execute(text("ALTER TABLE products ADD COLUMN competitors_json VARCHAR;"))
            await session.commit()
        except Exception:
            await session.rollback()
            
        # Pazarama test siparişlerini temizle (Geçmişte çekilmiş olanları siler)
        try:
            await session.execute(text("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE LOWER(order_number) LIKE '%test%' OR LOWER(customer_name) LIKE '%test%')"))
            await session.execute(text("DELETE FROM orders WHERE LOWER(order_number) LIKE '%test%' OR LOWER(customer_name) LIKE '%test%'"))
            
            # Kullanıcının talebi üzerine tüm n11 linklerini ve fırsat raporu verilerini komple sıfırlıyoruz.
            await session.execute(text("UPDATE products SET n11_url = NULL, competitors_json = '[]', cheapest_competitor_price = 0, last_repricing_check = NULL"))
            
            await session.commit()
            print("[Lifespan] Test siparişleri ve N11 Fırsat Raporu verileri tamamen sıfırlandı.")
        except Exception as e:
            await session.rollback()
            print(f"[Lifespan] Test siparişleri temizlenirken hata: {e}")

    # Uygulama başladığında devriyeyi arka plan görevi olarak başlat
    task = asyncio.create_task(order_patrol_loop())
    # Geçici olarak otomatik repricing durduruldu (kullanıcı talebi)
    # repricing_task = asyncio.create_task(repricing_loop())
    yield
    # Kapanışta iptal et (isterseniz task.cancel() eklenebilir)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.api import api_router

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"message": "Entegrasyon API is running!"}
