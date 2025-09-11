from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from ..config.database import get_db
from ..models.order import Order, OrderStatus
from ..schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from ..services.order_service import OrderService
from ..services.auth_service import AuthService
from ..celery_tasks.tasks import send_order_notification, send_order_confirmation_email
from ..utils.logger import logger

router = APIRouter(prefix="/orders", tags=["Orders"])

async def get_current_user_id(firebase_token: str, db: AsyncSession = Depends(get_db)) -> int:
    """Dependency to get current user ID"""
    user = await AuthService.create_or_get_user(db, firebase_token)
    return user.id

@router.post("/create", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Create order from cart"""
    user = await AuthService.create_or_get_user(db, firebase_token)
    order = await OrderService.create_order(db, user.id, order_data)
    
    # Send notifications with error handling
    try:
        if user.fcm_token:
            send_order_notification.delay([user.fcm_token], order.id, "confirmed")
        
        if user.email:
            send_order_confirmation_email.delay(user.email, order.id, order.total_amount)
    except Exception as e:
        logger.warning(f"Failed to queue notification tasks: {e}")
    
    return order

@router.get("/user/{user_id}", response_model=List[OrderResponse])
async def get_user_orders(
    user_id: int,
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get user's order history"""
    result = await db.execute(
        select(Order).options(
            selectinload(Order.items).selectinload(Order.items.product)
        ).where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .offset(offset).limit(limit)
    )
    orders = result.scalars().all()
    return [OrderResponse.model_validate(order) for order in orders]

@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_orders(
    user_id: int = Depends(get_current_user_id),
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's orders"""
    return await get_user_orders(user_id, limit, offset, db)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get specific order"""
    result = await db.execute(
        select(Order).options(
            selectinload(Order.items).selectinload(Order.items.product)
        ).where(Order.id == order_id, Order.user_id == user_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    return OrderResponse.model_validate(order)

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update order status (admin/delivery partner only)"""
    order = await OrderService.update_order_status(db, order_id, status_update.status)
    
    # Send notification to user
    result = await db.execute(select(Order).where(Order.id == order_id))
    order_obj = result.scalar_one()
    
    # Get user FCM token
    from ..models.user import User
    result = await db.execute(select(User).where(User.id == order_obj.user_id))
    user = result.scalar_one()
    
    try:
        if user.fcm_token:
            send_order_notification.delay([user.fcm_token], order_id, status_update.status.value)
    except Exception as e:
        logger.warning(f"Failed to queue notification task: {e}")
    
    return order