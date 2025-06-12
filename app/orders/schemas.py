from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.orders.models import OrderStatus

class OrderItemDetail(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    price: float
    total: float

    class Config:
        from_attributes = True

class OrderInfo(BaseModel):
    id:int
    total:float
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemDetail]

    class Config:
        from_attribute = True

class OrderSummary(BaseModel):
    id: int
    total: float
    status: OrderStatus
    created_at: datetime

    class Config:
        from_attribute = True
    
