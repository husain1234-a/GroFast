from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..schemas.user import OTPVerifyRequest, GoogleLoginRequest, UserResponse, UserUpdate
from ..services.auth_service import AuthService
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from custom_logging import setup_logging

logger = setup_logging("auth-service", log_level="INFO")

router = APIRouter()

@router.post("/verify-otp", response_model=UserResponse)
async def verify_otp(
    request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify Firebase OTP and create/get user"""
    logger.info(f"OTP verification request for token: {request.firebase_id_token[:10]}...")
    user = await AuthService.create_or_get_user(db, request.firebase_id_token)
    return UserResponse.model_validate(user)

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current user info"""
    logger.info(f"Get current user request for token: {firebase_token[:10]}...")
    user = await AuthService.create_or_get_user(db, firebase_token)
    return UserResponse.model_validate(user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Update current user info"""
    logger.info(f"Update user request for token: {firebase_token[:10]}...")
    user = await AuthService.create_or_get_user(db, firebase_token)
    updated_user = await AuthService.update_user(db, user.id, user_update)
    return UserResponse.model_validate(updated_user)

@router.post("/google-login", response_model=UserResponse)
async def google_login(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with Google OAuth"""
    logger.info("Google login request")
    user = await AuthService.create_or_get_user_google(db, request.google_id_token)
    return UserResponse.model_validate(user)

@router.post("/logout")
async def logout_user(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Logout user and invalidate session"""
    try:
        user = await AuthService.create_or_get_user(db, firebase_token)
        session_key = f"session:{user.id}:{firebase_token[-8:]}"
        await AuthService.invalidate_session(session_key)
        logger.info(f"User {user.id} logged out successfully")
        return {"message": "Logged out successfully"}
    except HTTPException:
        return {"message": "Logged out successfully"}

@router.post("/validate-token")
async def validate_firebase_token(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate Firebase token and return user info"""
    try:
        user = await AuthService.create_or_get_user(db, firebase_token)
        session_key = await AuthService.create_user_session(user.id, firebase_token)
        
        return {
            "valid": True,
            "user": UserResponse.model_validate(user),
            "session_key": session_key
        }
    except HTTPException as e:
        return {
            "valid": False,
            "error": e.detail
        }