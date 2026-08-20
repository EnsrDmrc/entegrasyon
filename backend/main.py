from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend portu
    allow_origin_regex=r"https://.*\.vercel\.app", # Vercel alan adlarına izin ver
    allow_credentials=True,
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
