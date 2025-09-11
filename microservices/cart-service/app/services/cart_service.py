from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.cart import Cart, CartItem
from ..schemas.cart import CartResponse, CartItemResponse
from fastapi import HTTPException

class CartService:
    @staticmethod
    async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
        result = await db.execute(select(Cart).where(Cart.user_id == user_id))
        cart = result.scalar_one_or_none()
        
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
        
        return cart
    
    @staticmethod
    async def get_cart_response(db: AsyncSession, user_id: int) -> CartResponse:
        # Try Redis cache first
        import redis.asyncio as redis
        try:
            redis_client = redis.from_url("redis://localhost:6379")
            cache_key = f"cart:user:{user_id}"
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                import json
                cart_data = json.loads(cached_data)
                return CartResponse(**cart_data)
        except Exception:
            pass
        
        cart = await CartService.get_or_create_cart(db, user_id)
        
        result = await db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id)
        )
        items = result.scalars().all()
        
        cart_items = []
        total_amount = 0
        total_items = 0
        
        # Get product details from product service
        for item in items:
            product_data = await CartService._get_product_details(item.product_id)
            price = product_data.get('price', 10.0)
            
            cart_item = CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=price,
                total_price=price * item.quantity,
                product_name=product_data.get('name', f"Product {item.product_id}"),
                product_image=product_data.get('image_url')
            )
            cart_items.append(cart_item)
            total_amount += cart_item.total_price
            total_items += item.quantity
        
        cart_response = CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=cart_items,
            total_amount=total_amount,
            total_items=total_items,
            created_at=cart.created_at,
            updated_at=cart.updated_at
        )
        
        # Cache the response
        try:
            await redis_client.setex(cache_key, 300, json.dumps(cart_response.model_dump(), default=str))
        except Exception:
            pass
        
        return cart_response
    
    @staticmethod
    async def add_to_cart(db: AsyncSession, user_id: int, product_id: int, quantity: int) -> CartResponse:
        # Validate product and check stock
        product_data = await CartService._get_product_details(product_id)
        if not product_data:
            raise HTTPException(status_code=404, detail="Product not found")
        
        stock_quantity = product_data.get('stock_quantity', 0)
        if stock_quantity < quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        cart = await CartService.get_or_create_cart(db, user_id)
        
        result = await db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == product_id
            )
        )
        existing_item = result.scalar_one_or_none()
        
        if existing_item:
            if stock_quantity < existing_item.quantity + quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock")
            existing_item.quantity += quantity
        else:
            new_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                price=product_data.get('price', 10.0)
            )
            db.add(new_item)
        
        await db.commit()
        
        # Invalidate cache
        await CartService._invalidate_cache(user_id)
        
        return await CartService.get_cart_response(db, user_id)
    
    @staticmethod
    async def remove_from_cart(db: AsyncSession, user_id: int, product_id: int) -> CartResponse:
        cart = await CartService.get_or_create_cart(db, user_id)
        
        result = await db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == product_id
            )
        )
        item = result.scalar_one_or_none()
        
        if item:
            await db.delete(item)
            await db.commit()
        
        # Invalidate cache
        await CartService._invalidate_cache(user_id)
        
        return await CartService.get_cart_response(db, user_id)
    
    @staticmethod
    async def clear_cart(db: AsyncSession, user_id: int):
        """Clear all items from cart"""
        cart = await CartService.get_or_create_cart(db, user_id)
        
        await db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id).delete()
        )
        await db.commit()
        
        # Invalidate cache
        await CartService._invalidate_cache(user_id)
    
    @staticmethod
    async def _get_product_details(product_id: int) -> dict:
        """Get product details from product service"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://product-service:8000/products/{product_id}")
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return {'id': product_id, 'name': f'Product {product_id}', 'price': 10.0, 'stock_quantity': 100}
    
    @staticmethod
    async def _invalidate_cache(user_id: int):
        """Invalidate cart cache"""
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url("redis://localhost:6379")
            cache_key = f"cart:user:{user_id}"
            await redis_client.delete(cache_key)
        except Exception:
            pass