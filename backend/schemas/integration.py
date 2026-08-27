from pydantic import BaseModel
from typing import Optional

class IntegrationCreate(BaseModel):
    marketplace_name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    store_url: Optional[str] = None
    is_active: bool = True

class IntegrationResponse(BaseModel):
    id: int
    marketplace_name: str
    store_url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True
