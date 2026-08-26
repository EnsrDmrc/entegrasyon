from pydantic import BaseModel
from typing import Optional

class ProductTransferRequest(BaseModel):
    sku: str
    source_marketplace: str
    target_marketplace: str
    target_category_id: str
    target_brand_id: str
    vat_rate: int = 20
