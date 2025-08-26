from fastapi import APIRouter, Request
import httpx
from ..config import settings

router = APIRouter()

@router.get("/categories")
async def get_categories(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.product_service_url}/categories")
        return response.json()

@router.get("/")
async def get_products(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.product_service_url}/products",
            params=dict(request.query_params)
        )
        return response.json()

@router.get("/{product_id}")
async def get_product(product_id: int, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.product_service_url}/products/{product_id}")
        return response.json()