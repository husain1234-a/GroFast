from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional
from datetime import datetime
import re

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    image_url: Optional[str] = Field(None, max_length=500, description="Category image URL")
    
    @validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Category name cannot be empty')
        if not re.match(r'^[a-zA-Z0-9\s\-&]+$', v):
            raise ValueError('Category name contains invalid characters')
        return v
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if v is not None:
            v = v.strip()
            if v and not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError('Image URL must start with http:// or https://')
        return v

class CategoryResponse(BaseModel):
    id: int
    name: str
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=1000, description="Product description")
    price: float = Field(..., gt=0, le=100000, description="Product price")
    mrp: Optional[float] = Field(None, gt=0, le=100000, description="Maximum retail price")
    category_id: int = Field(..., gt=0, description="Category ID")
    image_url: Optional[str] = Field(None, max_length=500, description="Product image URL")
    stock_quantity: int = Field(..., ge=0, le=10000, description="Stock quantity")
    unit: Optional[str] = Field(None, max_length=20, description="Unit of measurement")
    
    @validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Product name cannot be empty')
        if not re.match(r'^[a-zA-Z0-9\s\-&\.\(\)]+$', v):
            raise ValueError('Product name contains invalid characters')
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 1000:
                raise ValueError('Description too long')
        return v
    
    @validator('mrp')
    def validate_mrp(cls, v, values):
        if v is not None and 'price' in values:
            if v < values['price']:
                raise ValueError('MRP cannot be less than selling price')
        return v
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if v is not None:
            v = v.strip()
            if v and not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError('Image URL must start with http:// or https://')
        return v
    
    @validator('unit')
    def validate_unit(cls, v):
        if v is not None:
            v = v.strip()
            valid_units = ['kg', 'g', 'l', 'ml', 'pcs', 'pack', 'box', 'bottle', 'can']
            if v.lower() not in valid_units:
                raise ValueError(f'Invalid unit. Must be one of: {", ".join(valid_units)}')
        return v

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0, le=100000)
    mrp: Optional[float] = Field(None, gt=0, le=100000)
    category_id: Optional[int] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)
    stock_quantity: Optional[int] = Field(None, ge=0, le=10000)
    unit: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Product name cannot be empty')
            if not re.match(r'^[a-zA-Z0-9\s\-&\.\(\)]+$', v):
                raise ValueError('Product name contains invalid characters')
        return v

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