from fastapi import APIRouter, Request
import httpx
from ..config import settings

router = APIRouter()

@router.post("/create")
async def create_order(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.order_service_url}/orders/create",
            content=body,
            params=dict(request.query_params),
            headers={"content-type": "application/json"}
        )
        return response.json()

@router.get("/my-orders")
async def get_my_orders(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.order_service_url}/orders/my-orders",
            params=dict(request.query_params),
            headers=dict(request.headers)
        )
        return response.json()

@router.get("/{order_id}")
async def get_order(order_id: int, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.order_service_url}/orders/{order_id}",
            params=dict(request.query_params),
            headers=dict(request.headers)
        )
        return response.json()

@router.put("/{order_id}/status")
async def update_order_status(order_id: int, request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{settings.order_service_url}/orders/{order_id}/status",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()