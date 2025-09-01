from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class OTPVerifyRequest(BaseModel):
    firebase_id_token: str

class GoogleLoginRequest(BaseModel):
    google_id_token: str

class UserCreate(BaseModel):
    firebase_uid: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    fcm_token: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    fcm_token: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    fcm_token: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True