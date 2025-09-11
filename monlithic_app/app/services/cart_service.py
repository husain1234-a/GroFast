"""
Cart Service Module

This module provides cart management functionality including Redis caching,
cart operations, and cart data retrieval with optimized performance.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from ..models.cart import Cart, CartItem
from ..models.product import Product
from ..schemas.cart import CartResponse, CartItemResponse
from fastapi import HTTPException, status
import redis.asyncio as redis
import json
from typing import Optional, Dict, Any
from ..config.settings import settings

class CartService:
    """
    Cart Service for managing shopping cart operations with Redis caching.
    
    This service provides comprehensive cart management including:
    - Cart creation and retrieval
    - Item addition and removal
    - Redis caching for performance optimization
    - Cache invalidation strategies
    """
    _redis_client: Optional[redis.Redis] = None
    
    @classmethod
    async def get_redis_client(cls) -> redis.Redis:
        """Get Redis client for caching"""
        if cls._redis_client is None:
            cls._redis_client = redis.from_url(settings.redis_url)
        return cls._redis_client
    
    @staticmethod
    async def _get_cart_cache_key(user_id: int) -> str:
        """
        Generate cache key for user cart.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            str: Redis cache key for the user's cart
        """
        return f"cart:user:{user_id}"
    
    @staticmethod
    async def _invalidate_cart_cache(user_id: int) -> None:
        """
        Invalidate cart cache for user.
        
        Args:
            user_id: The user's unique identifier
        """
        try:
            redis_client = await CartService.get_redis_client()
            cache_key = await CartService._get_cart_cache_key(user_id)
            await redis_client.delete(cache_key)
        except Exception as e:
            # Log but don't fail if cache invalidation fails
            print(f"Cache invalidation failed: {e}")
    
    @staticmethod
    async def _get_cached_cart(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cart from cache.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            Optional[Dict[str, Any]]: Cached cart data or None if not found
        """
        try:
            redis_client = await CartService.get_redis_client()
            cache_key = await CartService._get_cart_cache_key(user_id)
            cached_data = await redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            # Log but don't fail if cache read fails
            print(f"Cache read failed: {e}")
        
        return None
    
    @staticmethod
    async def _cache_cart(user_id: int, cart_data: Dict[str, Any], ttl: int = 300) -> None:
        """
        Cache cart data with TTL.
        
        Args:
            user_id: The user's unique identifier
            cart_data: Cart data to cache
            ttl: Time to live in seconds (default: 5 minutes)
        """
        try:
            redis_client = await CartService.get_redis_client()
            cache_key = await CartService._get_cart_cache_key(user_id)
            await redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(cart_data, default=str)
            )
        except Exception as e:
            # Log but don't fail if cache write fails
            print(f"Cache write failed: {e}")
    
    @staticmethod
    async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
        """
        Get existing cart or create new one for user.
        
        Args:
            db: Database session
            user_id: The user's unique identifier
            
        Returns:
            Cart: User's cart instance
        """
        result = await db.execute(
            select(Cart).options(
                selectinload(Cart.items).selectinload(CartItem.product)
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
    async def add_to_cart(db: AsyncSession, user_id: int, product_id: int, quantity: int) -> CartResponse:
        """Add item to cart"""
        # Verify product exists
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        cart = await CartService.get_or_create_cart(db, user_id)
        
        # Check if item already in cart
        result = await db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        )
        cart_item = result.scalar_one_or_none()
        
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            db.add(cart_item)
        
        await db.commit()
        
        # Invalidate cache after modification
        await CartService._invalidate_cart_cache(user_id)
        
        return await CartService.get_cart_response(db, user_id)
    
    @staticmethod
    async def remove_from_cart(db: AsyncSession, user_id: int, product_id: int) -> CartResponse:
        """Remove item from cart"""
        cart = await CartService.get_or_create_cart(db, user_id)
        
        await db.execute(
            delete(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        )
        await db.commit()
        
        # Invalidate cache after modification
        await CartService._invalidate_cart_cache(user_id)
        
        return await CartService.get_cart_response(db, user_id)
    
    @staticmethod
    async def get_cart_response(db: AsyncSession, user_id: int) -> CartResponse:
        """Get cart with calculated totals (with caching)"""
        # Try to get from cache first
        cached_cart = await CartService._get_cached_cart(user_id)
        if cached_cart:
            return CartResponse(**cached_cart)
        
        # If not in cache, get from database
        cart = await CartService.get_or_create_cart(db, user_id)
        
        # Reload with items
        result = await db.execute(
            select(Cart).options(
                selectinload(Cart.items).selectinload(CartItem.product)
            ).where(Cart.id == cart.id)
        )
        cart = result.scalar_one()
        
        total_amount = sum(item.product.price * item.quantity for item in cart.items)
        total_items = sum(item.quantity for item in cart.items)
        
        cart_response = CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=[CartItemResponse.model_validate(item) for item in cart.items],
            total_amount=total_amount,
            total_items=total_items,
            created_at=cart.created_at
        )
        
        # Cache the response
        await CartService._cache_cart(user_id, cart_response.model_dump())
        
        return cart_response
    
    @staticmethod
    async def clear_cart(db: AsyncSession, user_id: int):
        """Clear all items from cart"""
        cart = await CartService.get_or_create_cart(db, user_id)
        
        await db.execute(
            delete(CartItem).where(CartItem.cart_id == cart.id)
        )
        await db.commit()
        
        # Invalidate cache after clearing
        await CartService._invalidate_cart_cache(user_id)