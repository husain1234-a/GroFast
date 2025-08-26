from fastapi import APIRouter, Request
import httpx
from ..config import settings

router = APIRouter()

@router.get("/me")
async def get_delivery_partner(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.delivery_service_url}/delivery/me",
            params=dict(request.query_params),
            headers=dict(request.headers)
        )
        return response.json()

@router.put("/status")
async def update_delivery_status(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{settings.delivery_service_url}/delivery/status",
            content=body,
            params=dict(request.query_params),
            headers={"content-type": "application/json"}
        )
        return response.json()

@router.post("/location")
async def update_location(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.delivery_service_url}/delivery/location",
            content=body,
            params=dict(request.query_params),
            headers={"content-type": "application/json"}
        )
        return response.json()

@router.get("/orders")
async def get_delivery_orders(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.delivery_service_url}/delivery/orders",
            params=dict(request.query_params),
            headers=dict(request.headers)
        )
        return response.json()