from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .product import ProductResponse

class CartItemBase(BaseModel):
    product_id: int
    quantity: int

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(CartItemBase):
    id: int
    product: ProductResponse
    created_at: datetime
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse] = []
    total_amount: float = 0
    total_items: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = 1

class RemoveFromCartRequest(BaseModel):
    product_id: int