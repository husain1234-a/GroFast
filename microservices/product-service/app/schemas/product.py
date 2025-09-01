from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    stock_quantity: int
    unit: str
    image_url: Optional[str] = None
    category_id: int
    category: Optional[CategoryResponse] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True