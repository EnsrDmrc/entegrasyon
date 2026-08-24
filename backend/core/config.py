from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Entegrasyon SaaS"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: Optional[str] = None
    DATABASE_URI: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = "localhost"
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = ""
    POSTGRES_DB: Optional[str] = "entegrasyon_db"
    POSTGRES_PORT: Optional[str] = "5432"

    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 7 gün

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Resend API (Railway gibi SMTP engelleyen yerlerde kullanmak için)
    RESEND_API_KEY: Optional[str] = None

    @property
    def ASYNC_DATABASE_URI(self) -> str:
        db_url = self.DATABASE_URL or self.DATABASE_URI
        if db_url:
            url = db_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
