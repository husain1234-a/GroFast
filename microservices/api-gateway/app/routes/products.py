from fastapi import APIRouter, Request
import sys
import os

# Add shared modules to path
shared_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared')
sys.path.append(shared_path)

from http_client import ResilientHttpClient
from custom_circuit_breaker import CircuitBreaker, RetryConfig, CircuitBreakerError
from ..config import settings

router = APIRouter()

# Create resilient HTTP client for product service
product_client = ResilientHttpClient(
    base_url=settings.product_service_url,
    timeout=5.0,
    circuit_breaker=CircuitBreaker(name="ProductService-Gateway"),
    retry_config=RetryConfig(max_attempts=3, base_delay=0.5)
)

@router.get("/categories")
async def get_categories(request: Request):
    try:
        response = await product_client.get("/categories")
        return response.json()
    except (CircuitBreakerError, Exception):
        # Fallback categories when service is unavailable
        return {
            "categories": [
                {"id": 1, "name": "Fruits & Vegetables", "fallback": True},
                {"id": 2, "name": "Dairy & Bakery", "fallback": True},
                {"id": 3, "name": "Snacks & Beverages", "fallback": True}
            ],
            "fallback": True
        }

@router.get("")
@router.get("/")
async def get_products(request: Request):
    try:
        response = await product_client.get(
            "/products",
            params=dict(request.query_params)
        )
        return response.json()
    except (CircuitBreakerError, Exception):
        # Fallback products when service is unavailable
        return {
            "products": [],
            "total": 0,
            "page": 1,
            "size": 20,
            "fallback": True,
            "message": "Product service temporarily unavailable"
        }

@router.get("/{product_id}")
async def get_product(product_id: int, request: Request):
    try:
        response = await product_client.get(f"/products/{product_id}")
        return response.json()
    except (CircuitBreakerError, Exception):
        # Fallback product when service is unavailable
        return {
            "id": product_id,
            "name": "Product Unavailable",
            "description": "Product service temporarily unavailable",
            "price": 0.0,
            "fallback": True
        }