from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..config.database import get_db
from ..schemas.user import OTPVerifyRequest, GoogleLoginRequest, UserResponse, UserUpdate
from ..services.auth_service import AuthService
from ..firebase.auth import verify_firebase_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/verify-otp", response_model=UserResponse)
async def verify_otp(
    request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify Firebase OTP and create/get user"""
    user = await AuthService.create_or_get_user(db, request.firebase_id_token)
    return UserResponse.model_validate(user)

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current user info"""
    user = await AuthService.create_or_get_user(db, firebase_token)
    return UserResponse.model_validate(user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Update current user info"""
    user = await AuthService.create_or_get_user(db, firebase_token)
    updated_user = await AuthService.update_user(db, user.id, user_update)
    return UserResponse.model_validate(updated_user)

@router.post("/google-login", response_model=UserResponse)
async def google_login(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with Google OAuth"""
    user = await AuthService.create_or_get_user_google(db, request.google_id_token)
    return UserResponse.model_validate(user)