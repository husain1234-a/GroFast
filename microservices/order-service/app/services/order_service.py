from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from ..models.order import Order, OrderItem, OrderStatus
from ..schemas.order import OrderCreate, OrderResponse
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import httpx

class OrderService:
    @staticmethod
    async def create_order(db: AsyncSession, user_id: int, order_data: OrderCreate) -> OrderResponse:
        # Get cart from Cart Service
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"http://localhost:8003/cart?firebase_token=user_{user_id}")
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="Failed to get cart")
                
                cart = response.json()
                if not cart["items"]:
                    raise HTTPException(status_code=400, detail="Cart is empty")
            except Exception as e:
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
        
        # Clear cart
        try:
            await client.delete(f"http://localhost:8003/cart/clear?firebase_token=user_{user_id}")
        except:
            pass  # Continue even if cart clear fails
        
        # Send notification
        try:
            await client.post("http://localhost:8006/notifications/order", json={
                "user_id": user_id,
                "order_id": order.id,
                "status": "confirmed"
            })
        except:
            pass  # Continue even if notification fails
        
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
        
        # Get product details for each item
        enriched_items = []
        for item in order.items:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://localhost:8002/products/{item.product_id}")
                    if response.status_code == 200:
                        product = response.json()
                        enriched_items.append({
                            "id": item.id,
                            "product_id": item.product_id,
                            "quantity": item.quantity,
                            "price": float(item.price),
                            "product_name": product["name"]
                        })
            except:
                enriched_items.append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "product_name": "Unknown Product"
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
            
            # Send notification
            try:
                async with httpx.AsyncClient() as client:
                    await client.post("http://localhost:8006/notifications/order", json={
                        "user_id": order.user_id,
                        "order_id": order.id,
                        "status": status.value
                    })
                    
                    # Send invoice email when order is delivered
                    if status == OrderStatus.DELIVERED:
                        order_response = await OrderService.get_order_response(db, order.id)
                        await client.post("http://localhost:8006/notifications/invoice-email", json={
                            "user_email": "customer@example.com",  # In real app, get from user table
                            "order_data": {
                                "id": order.id,
                                "total_amount": float(order.total_amount),
                                "delivery_fee": float(order.delivery_fee),
                                "delivery_address": order.delivery_address,
                                "items": order_response.items
                            }
                        })
            except:
                pass
        
        return await OrderService.get_order_response(db, order.id) if order else None