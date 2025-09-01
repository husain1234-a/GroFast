from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from ..database import get_db
from ..models.product import Product, Category
from ..schemas.product import ProductResponse, CategoryResponse
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from custom_logging import setup_logging

logger = setup_logging("product-service", log_level="INFO")

router = APIRouter()

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all active categories"""
    logger.info("Fetching all categories")
    result = await db.execute(
        select(Category).where(Category.is_active == True)
    )
    categories = result.scalars().all()
    logger.info(f"Found {len(categories)} categories")
    return [CategoryResponse.model_validate(cat) for cat in categories]

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search products by name"),
    limit: int = Query(50, le=100, description="Maximum number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
    db: AsyncSession = Depends(get_db)
):
    """Get products with optional filtering and pagination"""
    logger.info(f"Fetching products - category_id: {category_id}, search: {search}, limit: {limit}, offset: {offset}")
    
    query = select(Product).options(
        selectinload(Product.category)
    ).where(Product.is_active == True)
    
    if category_id:
        query = query.where(Product.category_id == category_id)
    
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    logger.info(f"Found {len(products)} products")
    return [ProductResponse.model_validate(product) for product in products]

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get product by ID"""
    logger.info(f"Fetching product with ID: {product_id}")
    result = await db.execute(
        select(Product).options(
            selectinload(Product.category)
        ).where(Product.id == product_id, Product.is_active == True)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        logger.warning(f"Product not found: {product_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return ProductResponse.model_validate(product)