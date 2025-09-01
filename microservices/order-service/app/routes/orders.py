from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from ..database import get_db
from ..models.order import Order, OrderStatus
from ..schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from ..services.order_service import OrderService
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from custom_logging import setup_logging

logger = setup_logging("order-service", log_level="INFO")

router = APIRouter()

async def get_user_id_from_header(x_user_id: str = Header(...)) -> int:
    """Get user ID from header (set by API Gateway)"""
    try:
        return int(x_user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid user ID")

@router.post("/create", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    user_id: int = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Create order from cart"""
    logger.info(f"Creating order for user {user_id}")
    order = await OrderService.create_order(db, user_id, order_data)
    logger.info(f"Order {order.id} created for user {user_id}")
    return order

@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_orders(
    user_id: int = Depends(get_user_id_from_header),
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's orders"""
    logger.info(f"Fetching orders for user {user_id}")
    result = await db.execute(
        select(Order).options(
            selectinload(Order.items).selectinload(Order.items.product)
        ).where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .offset(offset).limit(limit)
    )
    orders = result.scalars().all()
    logger.info(f"Found {len(orders)} orders for user {user_id}")
    return [OrderResponse.model_validate(order) for order in orders]

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    user_id: int = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Get specific order"""
    logger.info(f"Fetching order {order_id} for user {user_id}")
    result = await db.execute(
        select(Order).options(
            selectinload(Order.items).selectinload(Order.items.product)
        ).where(Order.id == order_id, Order.user_id == user_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        logger.warning(f"Order {order_id} not found for user {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    return OrderResponse.model_validate(order)

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update order status (admin/delivery partner only)"""
    logger.info(f"Updating order {order_id} status to {status_update.status}")
    order = await OrderService.update_order_status(db, order_id, status_update.status)
    logger.info(f"Order {order_id} status updated to {status_update.status}")
    return order