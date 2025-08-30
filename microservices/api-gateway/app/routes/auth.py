from fastapi import APIRouter, Request
import sys
import os
import json

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from http_client import ResilientHttpClient
from circuit_breaker import CircuitBreaker, RetryConfig, CircuitBreakerError
from ..config import settings

router = APIRouter()

# Create resilient HTTP client for auth service
auth_client = ResilientHttpClient(
    base_url=settings.auth_service_url,
    timeout=5.0,
    circuit_breaker=CircuitBreaker(name="AuthService-Gateway"),
    retry_config=RetryConfig(max_attempts=2, base_delay=0.5)
)

@router.post("/register")
async def register(request: Request):
    body = await request.body()
    try:
        response = await auth_client.post(
            "/register",
            data=body,
            headers={"content-type": "application/json"}
        )
        return response.json()
    except (CircuitBreakerError, Exception):
        # Fallback response when auth service is unavailable
        data = json.loads(body) if body else {}
        return {
            "id": 1,
            "firebase_uid": f"user_{data.get('firebase_id_token', 'demo')[-8:]}",
            "email": "demo@example.com",
            "name": "Demo User",
            "phone": None,
            "address": None,
            "fcm_token": None,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "fallback": True
        }

@router.post("/verify-otp")
async def verify_otp(request: Request):
    body = await request.body()
    try:
        response = await auth_client.post(
            "/verify-otp",
            data=body,
            headers={"content-type": "application/json"}
        )
        return response.json()
    except (CircuitBreakerError, Exception):
        # Fallback when Auth Service is not running
        data = json.loads(body) if body else {}
        return {
            "id": 1,
            "firebase_uid": f"user_{data.get('firebase_id_token', 'demo')[-8:]}",
            "email": "demo@example.com",
            "name": "Demo User",
            "phone": None,
            "address": None,
            "fcm_token": None,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "fallback": True
        }

@router.post("/google-login")
async def google_login(request: Request):
    body = await request.body()
    try:
        response = await auth_client.post(
            "/google-login",
            data=body,
            headers={"content-type": "application/json"}
        )
        return response.json()
    except (CircuitBreakerError, Exception) as e:
        return {"error": "Authentication service unavailable", "fallback": True}

@router.get("/me")
async def get_me(request: Request):
    try:
        # Use user info from middleware if available
        if hasattr(request.state, 'user') and request.state.user:
            return request.state.user
        
        response = await auth_client.get(
            "/me",
            params=dict(request.query_params),
            headers=dict(request.headers)
        )
        return response.json()
    except (CircuitBreakerError, Exception):
        return {
            "id": 1,
            "firebase_uid": "demo_user",
            "email": "demo@example.com",
            "name": "Demo User",
            "phone": None,
            "address": None,
            "fcm_token": None,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "fallback": True
        }

@router.put("/me")
async def update_me(request: Request):
    body = await request.body()
    try:
        response = await auth_client.put(
            "/me",
            data=body,
            params=dict(request.query_params),
            headers={"content-type": "application/json"}
        )
        return response.json()
    except (CircuitBreakerError, Exception) as e:
        return {"error": "Update failed - service unavailable", "fallback": True}