from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class MarketplaceIntegration(Base):
    __tablename__ = "marketplace_integrations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    marketplace_name = Column(String, nullable=False, index=True) # örn: 'shopify', 'n11'
    is_active = Column(Boolean, default=True)
    
    # Şifreli/Gizli bilgiler (API Keys vs.)
    api_key = Column(String, nullable=True)
    api_secret = Column(String, nullable=True)
    store_url = Column(String, nullable=True) # Shopify için "magaza.myshopify.com"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant")
