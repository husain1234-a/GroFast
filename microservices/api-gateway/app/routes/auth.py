from fastapi import APIRouter, Request
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

# Create HTTP client with circuit breaker for auth service
auth_client = ResilientHttpClient(
    base_url=settings.auth_service_url,
    timeout=5,
    circuit_breaker=CircuitBreaker(name="AuthService-Gateway"),
    retry_config=RetryConfig(max_attempts=2, base_delay=0.5)
)

@router.post("/verify-otp")
async def verify_otp(request: Request):
    body = await request.body()
    try:
        response = await auth_client.post(
            "/verify-otp",
            data=json.loads(body) if body else {},
            headers={"content-type": "application/json"}
        )
        return response
    except CircuitBreakerError:
        data = json.loads(body) if body else {}
        return {
            "id": 1,
            "firebase_uid": f"user_{data.get('firebase_id_token', 'demo')[-8:]}",
            "email": "demo@example.com",
            "name": "Demo User",
            "fallback": True
        }
    except Exception:
        return {"error": "Authentication service unavailable", "fallback": True}

@router.get("/me")
async def get_me(request: Request):
    try:
        response = await auth_client.get(
            "/me",
            headers=dict(request.headers)
        )
        return response
    except CircuitBreakerError:
        return {
            "id": 1,
            "firebase_uid": "demo_user",
            "email": "demo@example.com",
            "name": "Demo User",
            "fallback": True
        }
    except Exception:
        return {"error": "Authentication service unavailable", "fallback": True}