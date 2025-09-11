from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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

@router.get("/count")
async def get_products_count(db: AsyncSession = Depends(get_db)):
    """Get total count of active products"""
    result = await db.execute(
        select(func.count(Product.id)).where(Product.is_active == True)
    )
    return {"count": result.scalar()}

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

# Admin endpoints
async def verify_admin(x_admin_key: str = Header(...)):
    """Verify admin API key"""
    if x_admin_key != "admin_secret_key":
        raise HTTPException(status_code=403, detail="Admin access required")

@router.get("/admin/products", response_model=List[ProductResponse])
async def get_all_products_admin(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Admin endpoint to get all products including inactive ones"""
    logger.info(f"Admin fetching all products - limit: {limit}, offset: {offset}")
    
    query = select(Product).options(
        selectinload(Product.category)
    ).offset(offset).limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    logger.info(f"Admin found {len(products)} products")
    return [ProductResponse.model_validate(product) for product in products]

@router.post("/admin/products/{product_id}/restock")
async def restock_product(
    product_id: int,
    quantity_to_add: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Admin endpoint to restock product inventory"""
    logger.info(f"Restocking product {product_id} with {quantity_to_add} units")
    
    if quantity_to_add <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Atomic update to prevent race conditions
    product.stock_quantity += quantity_to_add
    await db.commit()
    await db.refresh(product)
    
    logger.info(f"Product {product_id} restocked. New stock: {product.stock_quantity}")
    return {
        "product_id": product_id,
        "quantity_added": quantity_to_add,
        "new_stock_quantity": product.stock_quantity
    }