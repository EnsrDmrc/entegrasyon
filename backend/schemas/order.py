from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderItemSchema(BaseModel):
    id: int
    product_sku: Optional[str]
    product_name: str
    quantity: int
    price: float

    class Config:
        from_attributes = True

class OrderSchema(BaseModel):
    id: int
    marketplace: str
    order_number: str
    customer_name: Optional[str]
    total_price: float
    status: str
    order_date: Optional[datetime]
    items: List[OrderItemSchema] = []

    class Config:
        from_attributes = True
