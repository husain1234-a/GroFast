from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, ForeignKey, 
    DateTime, CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config.database import Base

class Category(Base):
    """Product category model for organizing products."""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    products = relationship("Product", back_populates="category")

class Product(Base):
    """Product model for storing product information and inventory."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, CheckConstraint('price > 0'), nullable=False)
    mrp = Column(Float, CheckConstraint('mrp > 0'))
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String(500))
    stock_quantity = Column(Integer, CheckConstraint('stock_quantity >= 0'), default=0)
    unit = Column(String(20))  # kg, gm, piece, liter
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_product_category_active', 'category_id', 'is_active'),
        Index('idx_product_name_search', 'name'),
    )
    
    category = relationship("Category", back_populates="products")