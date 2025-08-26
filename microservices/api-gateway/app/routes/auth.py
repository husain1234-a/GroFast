from fastapi import APIRouter, Request
import httpx
from ..config import settings

router = APIRouter()

@router.post("/register")
async def register(request: Request):
    body = await request.body()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.auth_service_url}/register",
                content=body,
                headers={"content-type": "application/json"},
                timeout=5.0
            )
            return response.json()
    except httpx.ConnectError:
        import json
        data = json.loads(body)
        return {
            "id": 1,
            "firebase_uid": f"user_{data.get('firebase_id_token', 'demo')[-8:]}",
            "email": "demo@example.com",
            "name": "Demo User",
            "phone": None,
            "address": None,
            "fcm_token": None,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z"
        }

@router.post("/verify-otp")
async def verify_otp(request: Request):
    body = await request.body()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.auth_service_url}/verify-otp",
                content=body,
                headers={"content-type": "application/json"},
                timeout=5.0
            )
            return response.json()
    except httpx.ConnectError:
        # Fallback when Auth Service is not running
        import json
        data = json.loads(body)
        return {
            "id": 1,
            "firebase_uid": f"user_{data.get('firebase_id_token', 'demo')[-8:]}",
            "email": "demo@example.com",
            "name": "Demo User",
            "phone": None,
            "address": None,
            "fcm_token": None,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z"
        }

@router.post("/google-login")
async def google_login(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.auth_service_url}/google-login",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

@router.get("/me")
async def get_me(request: Request):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/me",
                params=dict(request.query_params),
                headers=dict(request.headers),
                timeout=5.0
            )
            return response.json()
    except httpx.ConnectError:
        return {
            "id": 1,
            "firebase_uid": "demo_user",
            "email": "demo@example.com",
            "name": "Demo User",
            "phone": None,
            "address": None,
            "fcm_token": None,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z"
        }

@router.put("/me")
async def update_me(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{settings.auth_service_url}/me",
            content=body,
            params=dict(request.query_params),
            headers={"content-type": "application/json"}
        )
        return response.json()