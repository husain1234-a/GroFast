from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.user import TokenVerifyRequest, UserResponse
from ..services.auth_service import AuthService
from ..database import get_db

router = APIRouter()

@router.post("/verify-token")
async def verify_token(
    request: TokenVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Internal endpoint for other services to verify tokens"""
    try:
        user = await AuthService.create_or_get_user(db, request.token)
        return {
            "valid": True,
            "user_id": user.id,
            "firebase_uid": user.firebase_uid
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Internal endpoint to get user info by ID"""
    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)