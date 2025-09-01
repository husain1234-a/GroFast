from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from ..database import get_db
from ..services.auth_service import AuthService
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from custom_logging import setup_logging

logger = setup_logging("auth-service-internal", log_level="INFO")

router = APIRouter()

class TokenVerifyRequest(BaseModel):
    token: str

@router.post("/verify-token")
async def verify_token(
    request: TokenVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Internal endpoint to verify token for other services"""
    try:
        user = await AuthService.create_or_get_user(db, request.token)
        logger.info(f"Token verified for user: {user.id}")
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active
        }
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/users/{user_id}")
async def get_user_info(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Internal endpoint to get user info by ID"""
    try:
        user = await AuthService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User info retrieved for user: {user_id}")
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "is_active": user.is_active,
            "fcm_token": user.fcm_token
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")