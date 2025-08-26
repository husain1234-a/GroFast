from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryResponse(BaseModel):
    id: int
    name: str
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    mrp: Optional[float]
    category_id: Optional[int]
    image_url: Optional[str]
    stock_quantity: int
    unit: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True