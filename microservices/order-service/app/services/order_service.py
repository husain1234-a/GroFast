from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from ..models.order import Order, OrderItem, OrderStatus
from ..schemas.order import OrderCreate, OrderResponse
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from http_client import ResilientHttpClient
from circuit_breaker import CircuitBreaker, RetryConfig

class OrderService:
    # Initialize resilient HTTP clients for external services
    _cart_client = None
    _product_client = None
    _notification_client = None
    
    @classmethod
    def get_cart_client(cls) -> ResilientHttpClient:
        if cls._cart_client is None:
            cls._cart_client = ResilientHttpClient(
                base_url="http://localhost:8003",
                timeout=5.0,
                circuit_breaker=CircuitBreaker(name="CartService"),
                retry_config=RetryConfig(max_attempts=3, base_delay=0.5)
            )
        return cls._cart_client
    
    @classmethod
    def get_product_client(cls) -> ResilientHttpClient:
        if cls._product_client is None:
            cls._product_client = ResilientHttpClient(
                base_url="http://localhost:8002",
                timeout=5.0,
                circuit_breaker=CircuitBreaker(name="ProductService"),
                retry_config=RetryConfig(max_attempts=3, base_delay=0.5)
            )
        return cls._product_client
    
    @classmethod
    def get_notification_client(cls) -> ResilientHttpClient:
        if cls._notification_client is None:
            cls._notification_client = ResilientHttpClient(
                base_url="http://localhost:8006",
                timeout=3.0,  # Shorter timeout for notifications
                circuit_breaker=CircuitBreaker(name="NotificationService"),
                retry_config=RetryConfig(max_attempts=2, base_delay=0.3)
            )
        return cls._notification_client
    
    @staticmethod
    async def create_order(db: AsyncSession, user_id: int, order_data: OrderCreate) -> OrderResponse:
        # Get cart from Cart Service using resilient client
        cart_client = OrderService.get_cart_client()
        try:
            response = await cart_client.get(f"/cart?firebase_token=user_{user_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get cart")
            
            cart = response.json()
            if not cart["items"]:
                raise HTTPException(status_code=400, detail="Cart is empty")
        except Exception as e:
            if "Circuit breaker" in str(e):
                raise HTTPException(status_code=503, detail="Cart service temporarily unavailable")
            else:
                raise HTTPException(status_code=400, detail="Failed to get cart")
        
        # Calculate totals
        total_amount = cart["total_amount"]
        delivery_fee = 20.0 if total_amount < 199 else 0.0
        
        # Create order
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            delivery_fee=delivery_fee,
            status=OrderStatus.PENDING,
            delivery_address=order_data.delivery_address,
            delivery_latitude=order_data.delivery_latitude,
            delivery_longitude=order_data.delivery_longitude,
            estimated_delivery_time=datetime.utcnow() + timedelta(minutes=30)
        )
        db.add(order)
        await db.flush()
        
        # Create order items
        for cart_item in cart["items"]:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item["product_id"],
                quantity=cart_item["quantity"],
                price=cart_item["product_price"]
            )
            db.add(order_item)
        
        await db.commit()
        await db.refresh(order)
        
        # Clear cart using resilient client
        try:
            await cart_client.delete(f"/cart/clear?firebase_token=user_{user_id}")
        except Exception as e:
            # Log but don't fail order creation if cart clear fails
            print(f"Warning: Failed to clear cart after order creation: {e}")
        
        # Send notification using resilient client
        notification_client = OrderService.get_notification_client()
        try:
            await notification_client.post("/notifications/order", json={
                "user_id": user_id,
                "order_id": order.id,
                "status": "confirmed"
            })
        except Exception as e:
            # Log but don't fail order creation if notification fails
            print(f"Warning: Failed to send order confirmation notification: {e}")
        
        return await OrderService.get_order_response(db, order.id)
    
    @staticmethod
    async def get_order_response(db: AsyncSession, order_id: int) -> OrderResponse:
        result = await db.execute(
            select(Order).options(
                selectinload(Order.items)
            ).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get product details for each item using resilient client
        enriched_items = []
        product_client = OrderService.get_product_client()
        
        for item in order.items:
            try:
                response = await product_client.get(f"/products/{item.product_id}")
                if response.status_code == 200:
                    product = response.json()
                    enriched_items.append({
                        "id": item.id,
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "price": float(item.price),
                        "product_name": product["name"]
                    })
                else:
                    # Product service error - use fallback
                    enriched_items.append({
                        "id": item.id,
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "price": float(item.price),
                        "product_name": "Product Unavailable"
                    })
            except Exception as e:
                # Circuit breaker or network error - use fallback
                enriched_items.append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "product_name": "Product Service Unavailable"
                })
        
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            total_amount=float(order.total_amount),
            delivery_fee=float(order.delivery_fee),
            status=order.status,
            delivery_address=order.delivery_address,
            items=enriched_items,
            created_at=order.created_at
        )
    
    @staticmethod
    async def get_user_orders(db: AsyncSession, user_id: int, limit: int = 20, offset: int = 0):
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        orders = result.scalars().all()
        return [await OrderService.get_order_response(db, order.id) for order in orders]
    
    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: int, user_id: int = None):
        query = select(Order).where(Order.id == order_id)
        if user_id:
            query = query.where(Order.user_id == user_id)
        
        result = await db.execute(query)
        order = result.scalar_one_or_none()
        if not order:
            return None
        return await OrderService.get_order_response(db, order.id)
    
    @staticmethod
    async def update_order_status(db: AsyncSession, order_id: int, status: OrderStatus):
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if order:
            order.status = status
            if status == OrderStatus.DELIVERED:
                order.delivered_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(order)
            
            # Send notification using resilient client
            notification_client = OrderService.get_notification_client()
            try:
                await notification_client.post("/notifications/order", json={
                    "user_id": order.user_id,
                    "order_id": order.id,
                    "status": status.value
                })
                
                # Send invoice email when order is delivered
                if status == OrderStatus.DELIVERED:
                    order_response = await OrderService.get_order_response(db, order.id)
                    await notification_client.post("/notifications/invoice-email", json={
                        "user_email": "customer@example.com",  # In real app, get from user table
                        "order_data": {
                            "id": order.id,
                            "total_amount": float(order.total_amount),
                            "delivery_fee": float(order.delivery_fee),
                            "delivery_address": order.delivery_address,
                            "items": order_response.items
                        }
                    })
            except Exception as e:
                # Log but don't fail status update if notification fails
                print(f"Warning: Failed to send order status notification: {e}")
        
        return await OrderService.get_order_response(db, order.id) if order else None