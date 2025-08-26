from fastapi import APIRouter, Request
import httpx
from ..config import settings

router = APIRouter()

@router.get("/")
async def get_cart(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.cart_service_url}/cart",
            params=dict(request.query_params),
            headers=dict(request.headers)
        )
        return response.json()

@router.post("/add")
async def add_to_cart(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.cart_service_url}/cart/add",
            content=body,
            params=dict(request.query_params),
            headers={"content-type": "application/json"}
        )
        return response.json()

@router.post("/remove")
async def remove_from_cart(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.cart_service_url}/cart/remove",
            content=body,
            params=dict(request.query_params),
            headers={"content-type": "application/json"}
        )
        return response.json()

@router.delete("/clear")
async def clear_cart(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{settings.cart_service_url}/cart/clear",
            params=dict(request.query_params),
            headers=dict(request.headers)
        )
        return response.json()