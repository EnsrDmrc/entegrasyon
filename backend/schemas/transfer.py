from pydantic import BaseModel
from typing import Optional

class ProductTransferRequest(BaseModel):
    sku: str
    source_marketplace: str
    target_marketplace: str
    target_category_id: int
    target_brand_id: int
    vat_rate: int = 20
