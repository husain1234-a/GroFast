from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderCreate(BaseModel):
    delivery_address: str
    delivery_time_slot: Optional[str] = None
    payment_method: str = "cash_on_delivery"
    notes: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    total_price: float
    product_name: Optional[str] = None

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total_amount: float
    delivery_address: str
    delivery_time_slot: Optional[str] = None
    payment_method: str
    notes: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True