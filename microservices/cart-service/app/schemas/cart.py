from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1

class RemoveFromCartRequest(BaseModel):
    product_id: int

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int
    price: float

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    total_price: float
    product_name: Optional[str] = None
    product_image: Optional[str] = None

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse] = []
    total_amount: float
    total_items: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True