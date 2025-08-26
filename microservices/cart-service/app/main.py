from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas.cart import CartItemCreate, CartItemRemove
from .services.cart_service import CartService
from .database import get_db

app = FastAPI(title="Cart Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

async def get_user_id(firebase_token: str = Query(...)):
    # Extract user ID from token (simplified)
    return int(firebase_token.split('_')[-1]) if '_' in firebase_token else 1

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Cart Service"}

@app.get("/cart")
async def get_cart(user_id: int = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    return await CartService.get_cart_with_details(db, user_id)

@app.post("/cart/add")
async def add_to_cart(item: CartItemCreate, user_id: int = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    return await CartService.add_item(db, user_id, item)

@app.post("/cart/remove")
async def remove_from_cart(item: CartItemRemove, user_id: int = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    return await CartService.remove_item(db, user_id, item.product_id)

@app.delete("/cart/clear")
async def clear_cart(user_id: int = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    return await CartService.clear_cart(db, user_id)