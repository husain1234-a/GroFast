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
    return UserResponse.model_validate(user)# S
ession management endpoints
@router.post("/logout")
async def logout_user(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Logout user and invalidate session"""
    try:
        user = await AuthService.create_or_get_user(db, firebase_token)
        
        # Invalidate session if using session management
        session_key = f"session:{user.id}:{firebase_token[-8:]}"
        await AuthService.invalidate_session(session_key)
        
        return {"message": "Logged out successfully"}
        
    except HTTPException:
        # Even if user validation fails, return success for logout
        return {"message": "Logged out successfully"}

@router.post("/logout-all")
async def logout_all_sessions(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Logout from all sessions"""
    user = await AuthService.create_or_get_user(db, firebase_token)
    
    invalidated_count = await AuthService.invalidate_all_user_sessions(user.id)
    
    return {
        "message": f"Logged out from {invalidated_count} sessions",
        "invalidated_sessions": invalidated_count
    }

@router.get("/sessions")
async def get_user_sessions(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all active sessions for current user"""
    user = await AuthService.create_or_get_user(db, firebase_token)
    
    sessions = await AuthService.get_user_sessions(user.id)
    
    return {
        "user_id": user.id,
        "active_sessions": len(sessions),
        "sessions": sessions
    }

@router.post("/refresh-session")
async def refresh_user_session(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh current user session"""
    user = await AuthService.create_or_get_user(db, firebase_token)
    
    session_key = f"session:{user.id}:{firebase_token[-8:]}"
    refreshed = await AuthService.refresh_session(session_key)
    
    if refreshed:
        return {"message": "Session refreshed successfully"}
    else:
        return {"message": "Session refresh failed or session not found"}

@router.post("/validate-token")
async def validate_firebase_token(
    firebase_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate Firebase token and return user info"""
    try:
        user = await AuthService.create_or_get_user(db, firebase_token)
        
        # Create or refresh session
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