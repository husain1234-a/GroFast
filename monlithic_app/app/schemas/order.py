from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .product import ProductResponse
from ..models.order import OrderStatus

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product: ProductResponse
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    delivery_address: str
    delivery_latitude: Optional[str] = None
    delivery_longitude: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    delivery_fee: float
    status: OrderStatus
    delivery_address: str
    delivery_latitude: Optional[str] = None
    delivery_longitude: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus