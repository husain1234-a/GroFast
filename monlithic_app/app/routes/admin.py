from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from ..config.database import get_db
from ..models.product import Product, Category
from ..models.order import Order, OrderStatus
from ..models.user import User
from ..schemas.product import ProductCreate, ProductUpdate, ProductResponse, CategoryCreate, CategoryResponse
from ..schemas.order import OrderResponse
from ..schemas.user import UserResponse
from ..services.notification_service import NotificationService, NotificationType, NotificationChannel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# Admin request models
class AdminNotificationRequest(BaseModel):
    user_ids: Optional[List[int]] = None  # If None, send to all users
    title: str
    body: str
    notification_type: NotificationType = NotificationType.PROMOTIONAL
    channels: List[NotificationChannel] = [NotificationChannel.FCM, NotificationChannel.IN_APP]

class BulkProductUpdateRequest(BaseModel):
    product_ids: List[int]
    updates: ProductUpdate

class AdminUserUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = None
    email: Optional[str] = None

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
# Enha
nced analytics endpoints
@router.get("/analytics/dashboard")
async def get_dashboard_analytics(
    days: int = Query(30, description="Number of days for analytics"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Get comprehensive dashboard analytics"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Revenue analytics
    revenue_result = await db.execute(
        select(func.sum(Order.total_amount))
        .where(and_(
            Order.status == OrderStatus.DELIVERED,
            Order.created_at >= start_date
        ))
    )
    period_revenue = revenue_result.scalar() or 0
    
    # Order analytics
    orders_result = await db.execute(
        select(func.count(Order.id))
        .where(Order.created_at >= start_date)
    )
    period_orders = orders_result.scalar() or 0
    
    # New users
    users_result = await db.execute(
        select(func.count(User.id))
        .where(User.created_at >= start_date)
    )
    new_users = users_result.scalar() or 0
    
    # Average order value
    avg_order_result = await db.execute(
        select(func.avg(Order.total_amount))
        .where(and_(
            Order.status == OrderStatus.DELIVERED,
            Order.created_at >= start_date
        ))
    )
    avg_order_value = avg_order_result.scalar() or 0
    
    # Top products
    top_products_result = await db.execute(
        select(
            Product.name,
            func.sum(OrderItem.quantity).label('total_sold')
        )
        .join(OrderItem)
        .join(Order)
        .where(Order.created_at >= start_date)
        .group_by(Product.id, Product.name)
        .order_by(desc('total_sold'))
        .limit(10)
    )
    top_products = [{"name": row[0], "quantity_sold": row[1]} for row in top_products_result.fetchall()]
    
    # Daily revenue trend
    daily_revenue_result = await db.execute(
        select(
            func.date(Order.created_at).label('date'),
            func.sum(Order.total_amount).label('revenue')
        )
        .where(and_(
            Order.status == OrderStatus.DELIVERED,
            Order.created_at >= start_date
        ))
        .group_by(func.date(Order.created_at))
        .order_by('date')
    )
    daily_revenue = [{"date": str(row[0]), "revenue": float(row[1])} for row in daily_revenue_result.fetchall()]
    
    return {
        "period_days": days,
        "revenue": {
            "total": float(period_revenue),
            "average_order_value": float(avg_order_value),
            "daily_trend": daily_revenue
        },
        "orders": {
            "total": period_orders,
            "new_users": new_users
        },
        "top_products": top_products,
        "summary": {
            "total_revenue": float(period_revenue),
            "total_orders": period_orders,
            "new_users": new_users,
            "avg_order_value": float(avg_order_value)
        }
    }

# User management endpoints
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Get all users with filtering"""
    query = select(User)
    
    if search:
        search_filter = or_(
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.phone.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    return [UserResponse.model_validate(user) for user in users]

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Update user details (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return {"message": "User updated successfully", "user": UserResponse.model_validate(user)}

# Bulk operations
@router.put("/products/bulk-update")
async def bulk_update_products(
    request: BulkProductUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Bulk update products"""
    updated_count = 0
    
    for product_id in request.product_ids:
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if product:
            for field, value in request.updates.model_dump(exclude_unset=True).items():
                setattr(product, field, value)
            updated_count += 1
    
    await db.commit()
    
    return {
        "message": f"Updated {updated_count} products",
        "updated_count": updated_count,
        "total_requested": len(request.product_ids)
    }

# Notification management
@router.post("/notifications/send")
async def send_admin_notification(
    request: AdminNotificationRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Send notification to users (admin only)"""
    service = NotificationService()
    
    # Get target users
    if request.user_ids:
        # Send to specific users
        result = await db.execute(select(User).where(User.id.in_(request.user_ids)))
        users = result.scalars().all()
    else:
        # Send to all active users
        result = await db.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()
    
    results = []
    
    for user in users:
        try:
            result = await service.send_notification(
                user_id=user.id,
                notification_type=request.notification_type,
                channels=request.channels,
                data={
                    "notification_type": request.notification_type.value,
                    "admin_message": True
                },
                fcm_token=user.fcm_token,
                email=user.email,
                phone=user.phone
            )
            results.append({"user_id": user.id, "success": True, "results": result})
        except Exception as e:
            results.append({"user_id": user.id, "success": False, "error": str(e)})
            logger.error(f"Failed to send notification to user {user.id}: {e}")
    
    successful_sends = sum(1 for r in results if r["success"])
    
    return {
        "message": f"Notification sent to {successful_sends}/{len(users)} users",
        "total_users": len(users),
        "successful_sends": successful_sends,
        "results": results
    }

# Order management enhancements
@router.put("/orders/{order_id}/status")
async def update_order_status_admin(
    order_id: int,
    status: OrderStatus,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Update order status (admin only)"""
    from ..services.order_service import OrderService
    
    try:
        updated_order = await OrderService.update_order_status(db, order_id, status)
        return {
            "message": "Order status updated successfully",
            "order": updated_order
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update order status")

# Inventory management
@router.get("/inventory/low-stock")
async def get_low_stock_products(
    threshold: int = Query(10, description="Stock threshold"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Get products with low stock"""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category))
        .where(and_(
            Product.stock_quantity <= threshold,
            Product.is_active == True
        ))
        .order_by(Product.stock_quantity.asc())
    )
    products = result.scalars().all()
    
    return {
        "threshold": threshold,
        "low_stock_count": len(products),
        "products": [ProductResponse.model_validate(product) for product in products]
    }

@router.put("/inventory/{product_id}/restock")
async def restock_product(
    product_id: int,
    quantity: int = Query(..., description="Quantity to add to stock"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Restock product"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    old_stock = product.stock_quantity
    product.stock_quantity += quantity
    
    await db.commit()
    await db.refresh(product)
    
    return {
        "message": "Product restocked successfully",
        "product_id": product_id,
        "old_stock": old_stock,
        "new_stock": product.stock_quantity,
        "added_quantity": quantity
    }

# System health and monitoring
@router.get("/system/health")
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Get system health status"""
    try:
        # Test database connection
        await db.execute(select(1))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check recent order activity
    recent_orders_result = await db.execute(
        select(func.count(Order.id))
        .where(Order.created_at >= datetime.utcnow() - timedelta(hours=1))
    )
    recent_orders = recent_orders_result.scalar() or 0
    
    # Check active users
    active_users_result = await db.execute(
        select(func.count(User.id))
        .where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "recent_activity": {
            "orders_last_hour": recent_orders,
            "active_users": active_users
        },
        "status": "healthy" if db_status == "healthy" else "degraded"
    }