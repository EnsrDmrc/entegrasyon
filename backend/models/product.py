from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    sku = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    
    # Yeni eklenen Pazarama entegrasyonu alanları
    pazarama_category_id = Column(String, nullable=True)
    pazarama_brand_id = Column(String, nullable=True)
    images_json = Column(String, nullable=True)
    
    # N11 Otomatik Fiyatlandırma için Ürün URL'si
    n11_url = Column(String, nullable=True)
    # Otomatik Fiyatlandırma (Repricing) Rapor Alanları
    is_expensive = Column(Integer, default=0) # 0: False, 1: True (Boolean yerine SQLite/Postgres uyumluluğu için veya direkt Boolean da olabilir ama DB'de boolean eklemek zordur, Integer kullanalım)
    our_cart_price = Column(Float, nullable=True)
    cheapest_competitor_price = Column(Float, nullable=True)
    cheapest_competitor_name = Column(String, nullable=True)
    last_repricing_check = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="products")
    inventories = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
