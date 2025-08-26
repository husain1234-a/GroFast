from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from .services.order_service import OrderService
from .database import get_db

app = FastAPI(title="Order Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

async def get_user_id(firebase_token: str = Query(...)):
    return int(firebase_token.split('_')[-1]) if '_' in firebase_token else 1

@app.get("/health")
async def health(): return {"status": "healthy", "service": "Order Service"}

@app.post("/orders/create", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    user_id: int = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    order = await OrderService.create_order(db, user_id, order_data)
    return OrderResponse.model_validate(order)

@app.get("/orders/my-orders", response_model=List[OrderResponse])
async def get_my_orders(
    user_id: int = Depends(get_user_id),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    orders = await OrderService.get_user_orders(db, user_id, limit, offset)
    return [OrderResponse.model_validate(order) for order in orders]

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    user_id: int = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    order = await OrderService.get_order_by_id(db, order_id, user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse.model_validate(order)

@app.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    order = await OrderService.update_order_status(db, order_id, status_update.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse.model_validate(order)