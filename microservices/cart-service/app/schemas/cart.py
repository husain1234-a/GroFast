from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_amount: float
    total_items: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CartItemRemove(BaseModel):
    product_id: int

class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1

class RemoveFromCartRequest(BaseModel):
    product_id: int