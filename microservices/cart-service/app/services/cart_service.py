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
        cart = await CartService.get_or_create_cart(db, user_id)
        
        result = await db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id)
        )
        items = result.scalars().all()
        
        cart_items = []
        total_amount = 0
        total_items = 0
        
        for item in items:
            cart_item = CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price,
                total_price=item.price * item.quantity,
                product_name=f"Product {item.product_id}",
                product_image=None
            )
            cart_items.append(cart_item)
            total_amount += cart_item.total_price
            total_items += item.quantity
        
        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=cart_items,
            total_amount=total_amount,
            total_items=total_items,
            created_at=cart.created_at,
            updated_at=cart.updated_at
        )
    
    @staticmethod
    async def add_to_cart(db: AsyncSession, user_id: int, product_id: int, quantity: int) -> CartResponse:
        cart = await CartService.get_or_create_cart(db, user_id)
        
        result = await db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == product_id
            )
        )
        existing_item = result.scalar_one_or_none()
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                price=10.0
            )
            db.add(new_item)
        
        await db.commit()
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
        
        return await CartService.get_cart_response(db, user_id)