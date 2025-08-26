from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..models.order import OrderStatus

class OrderCreate(BaseModel):
    delivery_address: str
    delivery_latitude: Optional[str] = None
    delivery_longitude: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    delivery_fee: float
    status: OrderStatus
    delivery_address: str
    items: List[OrderItemResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus