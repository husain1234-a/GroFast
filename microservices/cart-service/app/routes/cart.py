from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..schemas.cart import CartResponse, AddToCartRequest, RemoveFromCartRequest
from ..services.cart_service import CartService
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from custom_logging import setup_logging

logger = setup_logging("cart-service", log_level="INFO")

router = APIRouter()

async def get_user_id_from_header(x_user_id: str = Header(...)) -> int:
    """Get user ID from header (set by API Gateway)"""
    try:
        return int(x_user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid user ID")

@router.get("/", response_model=CartResponse)
async def get_cart(
    user_id: int = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Get user's cart"""
    logger.info(f"Fetching cart for user: {user_id}")
    cart = await CartService.get_cart_response(db, user_id)
    logger.info(f"Cart fetched for user {user_id} with {len(cart.items)} items")
    return cart

@router.post("/add", response_model=CartResponse)
async def add_to_cart(
    request: AddToCartRequest,
    user_id: int = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Add item to cart"""
    logger.info(f"Adding product {request.product_id} (qty: {request.quantity}) to cart for user {user_id}")
    cart = await CartService.add_to_cart(db, user_id, request.product_id, request.quantity)
    logger.info(f"Product added to cart for user {user_id}")
    return cart

@router.post("/remove", response_model=CartResponse)
async def remove_from_cart(
    request: RemoveFromCartRequest,
    user_id: int = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Remove item from cart"""
    logger.info(f"Removing product {request.product_id} from cart for user {user_id}")
    cart = await CartService.remove_from_cart(db, user_id, request.product_id)
    logger.info(f"Product removed from cart for user {user_id}")
    return cart

@router.delete("/clear", response_model=CartResponse)
async def clear_cart(
    user_id: int = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Clear all items from cart"""
    logger.info(f"Clearing cart for user {user_id}")
    cart = await CartService.get_or_create_cart(db, user_id)
    from sqlalchemy import delete
    from ..models.cart import CartItem
    
    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await db.commit()
    
    result = await CartService.get_cart_response(db, user_id)
    logger.info(f"Cart cleared for user {user_id}")
    return result