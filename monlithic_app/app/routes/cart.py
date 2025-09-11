from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.database import get_db
from ..schemas.cart import CartResponse, AddToCartRequest, RemoveFromCartRequest
from ..services.cart_service import CartService
from ..services.auth_service import AuthService

router = APIRouter(prefix="/cart", tags=["Cart"])

async def get_current_user_id(firebase_token: str, db: AsyncSession = Depends(get_db)) -> int:
    """Dependency to get current user ID"""
    user = await AuthService.create_or_get_user(db, firebase_token)
    return user.id

@router.get("/", response_model=CartResponse)
async def get_cart(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's cart"""
    return await CartService.get_cart_response(db, user_id)

@router.post("/add", response_model=CartResponse)
async def add_to_cart(
    request: AddToCartRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Add item to cart"""
    return await CartService.add_to_cart(db, user_id, request.product_id, request.quantity)

@router.post("/remove", response_model=CartResponse)
async def remove_from_cart(
    request: RemoveFromCartRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove item from cart"""
    return await CartService.remove_from_cart(db, user_id, request.product_id)

@router.delete("/clear", response_model=CartResponse)
async def clear_cart(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Clear all items from cart"""
    cart = await CartService.get_or_create_cart(db, user_id)
    from sqlalchemy import delete
    from ..models.cart import CartItem
    
    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await db.commit()
    
    return await CartService.get_cart_response(db, user_id)