from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from ..models.cart import Cart, CartItem
from ..models.product import Product
from ..schemas.cart import CartResponse, CartItemResponse
from fastapi import HTTPException, status

class CartService:
    @staticmethod
    async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
        """Get or create user cart"""
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
        return await CartService.get_cart_response(db, user_id)
    
    @staticmethod
    async def remove_from_cart(db: AsyncSession, user_id: int, product_id: int) -> CartResponse:
        """Remove item from cart"""
        cart = await CartService.get_or_create_cart(db, user_id)
        
        await db.execute(
            delete(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        )
        await db.commit()
        return await CartService.get_cart_response(db, user_id)
    
    @staticmethod
    async def get_cart_response(db: AsyncSession, user_id: int) -> CartResponse:
        """Get cart with calculated totals"""
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
        
        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=[CartItemResponse.model_validate(item) for item in cart.items],
            total_amount=total_amount,
            total_items=total_items,
            created_at=cart.created_at
        )