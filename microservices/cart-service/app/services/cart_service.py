from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from ..models.cart import Cart, CartItem
from ..schemas.cart import CartResponse, CartItemResponse, CartItemCreate
from fastapi import HTTPException, status
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from http_client import ResilientHttpClient
from circuit_breaker import CircuitBreaker, RetryConfig

class CartService:
    # Initialize resilient HTTP clients for external services
    _product_client = None
    
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
    
    @staticmethod
    async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
        result = await db.execute(
            select(Cart).options(
                selectinload(Cart.items)
            ).where(Cart.user_id == user_id)
        )
        cart = result.scalar_one_or_none()
        
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
        
        return cart
    
    @staticmethod
    async def add_item(db: AsyncSession, user_id: int, item_data: CartItemCreate):
        # Verify product exists via Product Service using resilient client
        product_client = CartService.get_product_client()
        try:
            response = await product_client.get(f"/products/{item_data.product_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Product not found")
        except Exception as e:
            # Circuit breaker or network error - use fallback
            if "Circuit breaker" in str(e):
                # Allow adding item even if product service is down (graceful degradation)
                pass
            else:
                raise HTTPException(status_code=404, detail="Product not found")
        
        cart = await CartService.get_or_create_cart(db, user_id)
        
        # Check if item already exists
        result = await db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == item_data.product_id
            )
        )
        existing_item = result.scalar_one_or_none()
        
        if existing_item:
            existing_item.quantity += item_data.quantity
        else:
            new_item = CartItem(
                cart_id=cart.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity
            )
            db.add(new_item)
        
        await db.commit()
        return await CartService.get_cart_response(db, user_id)
    
    @staticmethod
    async def remove_item(db: AsyncSession, user_id: int, product_id: int):
        cart = await CartService.get_or_create_cart(db, user_id)
        
        await db.execute(
            delete(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == product_id
            )
        )
        await db.commit()
        return await CartService.get_cart_response(db, user_id)
    
    @staticmethod
    async def clear_cart(db: AsyncSession, user_id: int):
        cart = await CartService.get_or_create_cart(db, user_id)
        await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        await db.commit()
        return await CartService.get_cart_response(db, user_id)
    
    @staticmethod
    async def get_cart_response(db: AsyncSession, user_id: int) -> CartResponse:
        cart = await CartService.get_or_create_cart(db, user_id)
        
        # Reload with items
        result = await db.execute(
            select(Cart).options(
                selectinload(Cart.items)
            ).where(Cart.id == cart.id)
        )
        cart = result.scalar_one()
        
        # Get product details for each item using resilient client
        enriched_items = []
        total_amount = 0
        product_client = CartService.get_product_client()
        
        for item in cart.items:
            try:
                response = await product_client.get(f"/products/{item.product_id}")
                if response.status_code == 200:
                    product = response.json()
                    item_total = product['price'] * item.quantity
                    total_amount += item_total
                    
                    enriched_items.append(CartItemResponse(
                        id=item.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        product_name=product['name'],
                        product_price=product['price'],
                        created_at=item.created_at
                    ))
                else:
                    # Product service returned error - use fallback
                    enriched_items.append(CartItemResponse(
                        id=item.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        product_name="Product Unavailable",
                        product_price=0,
                        created_at=item.created_at
                    ))
            except Exception as e:
                # Circuit breaker or network error - use fallback data
                enriched_items.append(CartItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    product_name="Product Service Unavailable",
                    product_price=0,
                    created_at=item.created_at
                ))
        
        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=enriched_items,
            total_amount=total_amount,
            total_items=sum(item.quantity for item in cart.items),
            created_at=cart.created_at
        )
    
    # Alias for compatibility
    get_cart_with_details = get_cart_response