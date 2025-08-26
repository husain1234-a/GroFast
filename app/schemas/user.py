from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class UserCreate(UserBase):
    firebase_uid: str
    fcm_token: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    fcm_token: Optional[str] = None

class UserResponse(UserBase):
    id: int
    firebase_uid: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    phone: str

class OTPVerifyRequest(BaseModel):
    firebase_id_token: str

class GoogleLoginRequest(BaseModel):
    google_id_token: str