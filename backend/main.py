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
        try:
            await session.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT TRUE;"))
            await session.execute(text("ALTER TABLE users ADD COLUMN otp_code VARCHAR;"))
            await session.execute(text("ALTER TABLE users ADD COLUMN otp_expires_at TIMESTAMP WITH TIME ZONE;"))
            await session.execute(text("UPDATE users SET is_verified = TRUE WHERE is_verified IS NULL;"))
            
            # Pazarama Güncellemeleri
            await session.execute(text("ALTER TABLE products ADD COLUMN pazarama_category_id VARCHAR;"))
            await session.execute(text("ALTER TABLE products ADD COLUMN pazarama_brand_id VARCHAR;"))
            await session.execute(text("ALTER TABLE products ADD COLUMN images_json VARCHAR;"))
            
            await session.commit()
        except Exception as e:
            print("Migration (ALTER TABLE) skipped or already applied:", e)

    # Uygulama başladığında devriyeyi arka plan görevi olarak başlat
    task = asyncio.create_task(order_patrol_loop())
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
