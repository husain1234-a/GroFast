from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.order import Order, OrderItem
from ..schemas.order import OrderCreate, OrderResponse, OrderStatus
from fastapi import HTTPException
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from custom_circuit_breaker import CircuitBreaker, RetryConfig, CircuitBreakerError

class OrderService:
    def __init__(self):
        self.cart_circuit_breaker = CircuitBreaker(name="CartService")
        self.notification_circuit_breaker = CircuitBreaker(name="NotificationService")
    
    @staticmethod
    async def create_order(db: AsyncSession, user_id: int, order_data: OrderCreate) -> OrderResponse:
        """Create order from cart with circuit breaker"""
        circuit_breaker = CircuitBreaker(name="OrderCreation")
        
        if circuit_breaker.is_open:
            raise CircuitBreakerError("Order creation circuit breaker is open")
        
        try:
            # Create order
            order = Order(
                user_id=user_id,
                status=OrderStatus.PENDING,
                total_amount=100.0,  # Mock amount
                delivery_address=order_data.delivery_address,
                delivery_time_slot=order_data.delivery_time_slot,
                payment_method=order_data.payment_method,
                notes=order_data.notes
            )
            
            db.add(order)
            await db.commit()
            await db.refresh(order)
            
            # Mock order items
            order_item = OrderItem(
                order_id=order.id,
                product_id=1,
                quantity=2,
                price=50.0,
                total_price=100.0
            )
            db.add(order_item)
            await db.commit()
            
            return OrderResponse(
                id=order.id,
                user_id=order.user_id,
                status=order.status,
                total_amount=order.total_amount,
                delivery_address=order.delivery_address,
                delivery_time_slot=order.delivery_time_slot,
                payment_method=order.payment_method,
                notes=order.notes,
                items=[],
                created_at=order.created_at,
                updated_at=order.updated_at
            )
        except Exception as e:
            circuit_breaker.is_open = True
            raise
    
    @staticmethod
    async def update_order_status(db: AsyncSession, order_id: int, status: OrderStatus) -> OrderResponse:
        """Update order status with circuit breaker"""
        circuit_breaker = CircuitBreaker(name="OrderStatusUpdate")
        
        if circuit_breaker.is_open:
            raise CircuitBreakerError("Order status update circuit breaker is open")
        
        try:
            result = await db.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            order.status = status
            await db.commit()
            await db.refresh(order)
            
            return OrderResponse(
                id=order.id,
                user_id=order.user_id,
                status=order.status,
                total_amount=order.total_amount,
                delivery_address=order.delivery_address,
                delivery_time_slot=order.delivery_time_slot,
                payment_method=order.payment_method,
                notes=order.notes,
                items=[],
                created_at=order.created_at,
                updated_at=order.updated_at
            )
        except Exception as e:
            circuit_breaker.is_open = True
            raise