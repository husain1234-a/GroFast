from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from ..models.order import Order, OrderItem, OrderStatus
from ..models.cart import Cart, CartItem
from ..models.user import User
from ..schemas.order import OrderCreate, OrderResponse
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import logging

# Import notification service
from .notification_service import notify_order_status_change

logger = logging.getLogger(__name__)

class OrderService:
    @staticmethod
    async def create_order(db: AsyncSession, user_id: int, order_data: OrderCreate) -> OrderResponse:
        """Create order from cart"""
        # Get user cart
        result = await db.execute(
            select(Cart).options(
                selectinload(Cart.items).selectinload(CartItem.product)
            ).where(Cart.user_id == user_id)
        )
        cart = result.scalar_one_or_none()
        
        if not cart or not cart.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
        
        # Calculate totals
        total_amount = sum(item.product.price * item.quantity for item in cart.items)
        delivery_fee = 20.0  # Fixed delivery fee
        
        # Create order
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            delivery_fee=delivery_fee,
            delivery_address=order_data.delivery_address,
            delivery_latitude=order_data.delivery_latitude,
            delivery_longitude=order_data.delivery_longitude,
            estimated_delivery_time=datetime.utcnow() + timedelta(minutes=30)
        )
        db.add(order)
        await db.flush()
        
        # Create order items
        for cart_item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.add(order_item)
        
        # Clear cart
        await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        
        await db.commit()
        await db.refresh(order)
        
        # Send order confirmation notification
        try:
            # Get user details for notification
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            
            if user:
                await notify_order_status_change(
                    user_id=user_id,
                    order_id=order.id,
                    status="confirmed",
                    fcm_token=user.fcm_token,
                    email=user.email,
                    phone=user.phone,
                    total_amount=total_amount + delivery_fee,
                    estimated_delivery="30-40 minutes"
                )
                logger.info(f"Order confirmation notification sent for order {order.id}")
        except Exception as e:
            logger.error(f"Failed to send order confirmation notification: {e}")
        
        return await OrderService.get_order_response(db, order.id)
    
    @staticmethod
    async def get_order_response(db: AsyncSession, order_id: int) -> OrderResponse:
        """Get order with items"""
        result = await db.execute(
            select(Order).options(
                selectinload(Order.items).selectinload(OrderItem.product)
            ).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        return OrderResponse.model_validate(order)
    
    @staticmethod
    async def update_order_status(db: AsyncSession, order_id: int, status: OrderStatus) -> OrderResponse:
        """Update order status"""
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        old_status = order.status
        order.status = status
        if status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()
        
        await db.commit()
        
        # Send status update notification if status changed
        if old_status != status:
            try:
                # Get user details for notification
                user_result = await db.execute(select(User).where(User.id == order.user_id))
                user = user_result.scalar_one_or_none()
                
                if user:
                    # Map OrderStatus enum to string
                    status_mapping = {
                        OrderStatus.PENDING: "confirmed",
                        OrderStatus.CONFIRMED: "confirmed", 
                        OrderStatus.PREPARING: "preparing",
                        OrderStatus.OUT_FOR_DELIVERY: "out_for_delivery",
                        OrderStatus.DELIVERED: "delivered",
                        OrderStatus.CANCELLED: "cancelled"
                    }
                    
                    status_str = status_mapping.get(status, "confirmed")
                    
                    await notify_order_status_change(
                        user_id=order.user_id,
                        order_id=order_id,
                        status=status_str,
                        fcm_token=user.fcm_token,
                        email=user.email,
                        phone=user.phone,
                        total_amount=order.total_amount + order.delivery_fee
                    )
                    logger.info(f"Order status update notification sent for order {order_id}: {status_str}")
            except Exception as e:
                logger.error(f"Failed to send order status notification: {e}")
        
        return await OrderService.get_order_response(db, order_id)