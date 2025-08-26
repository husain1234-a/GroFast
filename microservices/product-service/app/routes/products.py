from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from ..models.product import Product, Category
from ..schemas.product import ProductResponse, CategoryResponse
from ..database import get_db

router = APIRouter()

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category).where(Category.is_active == True)
    )
    categories = result.scalars().all()
    return [CategoryResponse.model_validate(cat) for cat in categories]

@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(Product).where(Product.is_active == True)
    
    if category_id:
        query = query.where(Product.category_id == category_id)
    
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    
    return [ProductResponse.model_validate(product) for product in products]

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)