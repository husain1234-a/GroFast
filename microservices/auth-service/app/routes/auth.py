from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.user import *
from ..services.auth_service import AuthService
from ..database import get_db

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(
    request: UserRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.create_or_get_user(db, request.firebase_id_token)
    
    if request.name or request.address or request.fcm_token:
        update_data = UserUpdate(
            name=request.name,
            address=request.address,
            fcm_token=request.fcm_token
        )
        user = await AuthService.update_user(db, user.id, update_data)
    
    return UserResponse.model_validate(user)

@router.post("/verify-otp", response_model=UserResponse)
async def verify_otp(
    request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.create_or_get_user(db, request.firebase_id_token)
    return UserResponse.model_validate(user)

@router.post("/google-login", response_model=UserResponse)
async def google_login(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.create_or_get_user_google(db, request.google_id_token)
    return UserResponse.model_validate(user)

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    firebase_token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.create_or_get_user(db, firebase_token)
    return UserResponse.model_validate(user)

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    firebase_token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.create_or_get_user(db, firebase_token)
    updated_user = await AuthService.update_user(db, user.id, user_update)
    return UserResponse.model_validate(updated_user)