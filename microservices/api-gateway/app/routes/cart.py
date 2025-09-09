from fastapi import APIRouter, Request, HTTPException
import sys
import os
import json

# Add shared modules to path
shared_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared')
sys.path.append(shared_path)

from http_client import ResilientHttpClient
from custom_circuit_breaker import CircuitBreaker, RetryConfig, CircuitBreakerError
from ..config import settings

router = APIRouter()

# Create resilient HTTP client for cart service
cart_client = ResilientHttpClient(
    base_url=settings.cart_service_url,
    timeout=5.0,
    circuit_breaker=CircuitBreaker(name="CartService-Gateway"),
    retry_config=RetryConfig(max_attempts=3, base_delay=0.5)
)

@router.get("")
@router.get("/")
async def get_cart(request: Request):
    try:
        # Forward authorization header
        headers = {}
        if "authorization" in request.headers:
            headers["authorization"] = request.headers["authorization"]
        
        response = await cart_client.get(
            "/cart",
            headers=headers,
            params=dict(request.query_params)
        )
        return response
    except CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Cart service temporarily unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cart service error: {str(e)}")

@router.post("/add")
async def add_to_cart(request: Request):
    try:
        # Get request body
        body = await request.json()
        
        # Forward authorization header
        headers = {}
        if "authorization" in request.headers:
            headers["authorization"] = request.headers["authorization"]
        
        response = await cart_client.post(
            "/cart/add",
            data=body,
            headers=headers
        )
        return response
    except CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Cart service temporarily unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cart service error: {str(e)}")

@router.post("/remove")
async def remove_from_cart(request: Request):
    try:
        # Get request body
        body = await request.json()
        
        # Forward authorization header
        headers = {}
        if "authorization" in request.headers:
            headers["authorization"] = request.headers["authorization"]
        
        response = await cart_client.post(
            "/cart/remove",
            data=body,
            headers=headers
        )
        return response
    except CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Cart service temporarily unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cart service error: {str(e)}")

@router.post("/clear")
async def clear_cart(request: Request):
    try:
        # Forward authorization header
        headers = {}
        if "authorization" in request.headers:
            headers["authorization"] = request.headers["authorization"]
        
        response = await cart_client.post(
            "/cart/clear",
            headers=headers
        )
        return response
    except CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Cart service temporarily unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cart service error: {str(e)}")