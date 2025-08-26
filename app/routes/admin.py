from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from ..config.database import get_db
from ..models.product import Product, Category
from ..models.order import Order, OrderStatus
from ..models.user import User
from ..schemas.product import ProductCreate, ProductUpdate, ProductResponse, CategoryCreate, CategoryResponse
from ..schemas.order import OrderResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

# Simple admin authentication (in production, use proper admin auth)
async def verify_admin(admin_key: str = Query(...)):
    """Simple admin verification"""
    if admin_key != "admin123":  # Change this in production
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")

@router.get("/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Get admin dashboard stats"""
    # Total users
    users_count = await db.execute(select(func.count(User.id)))
    total_users = users_count.scalar()
    
    # Total orders
    orders_count = await db.execute(select(func.count(Order.id)))
    total_orders = orders_count.scalar()
    
    # Total revenue
    revenue_result = await db.execute(select(func.sum(Order.total_amount)).where(Order.status == OrderStatus.DELIVERED))
    total_revenue = revenue_result.scalar() or 0
    
    # Orders by status
    status_counts = {}
    for status in OrderStatus:
        count_result = await db.execute(select(func.count(Order.id)).where(Order.status == status))
        status_counts[status.value] = count_result.scalar()
    
    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "orders_by_status": status_counts
    }

@router.get("/products", response_model=List[ProductResponse])
async def get_all_products(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Get all products for admin"""
    result = await db.execute(
        select(Product).options(selectinload(Product.category))
    )
    products = result.scalars().all()
    return [ProductResponse.model_validate(product) for product in products]

@router.post("/products", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Create new product"""
    product = Product(**product_data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return ProductResponse.model_validate(product)

@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Update product"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    for field, value in product_update.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    return ProductResponse.model_validate(product)

@router.get("/categories", response_model=List[CategoryResponse])
async def get_all_categories(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Get all categories for admin"""
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return [CategoryResponse.model_validate(cat) for cat in categories]

@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Create new category"""
    category = Category(**category_data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return CategoryResponse.model_validate(category)

@router.get("/orders", response_model=List[OrderResponse])
async def get_all_orders(
    status: OrderStatus = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Get all orders for admin"""
    query = select(Order).options(
        selectinload(Order.items).selectinload(Order.items.product)
    )
    
    if status:
        query = query.where(Order.status == status)
    
    query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    return [OrderResponse.model_validate(order) for order in orders]