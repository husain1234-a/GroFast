from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    firebase_uid: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    fcm_token: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    fcm_token: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    phone: Optional[str]
    email: Optional[EmailStr]
    name: Optional[str]
    address: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class OTPVerifyRequest(BaseModel):
    firebase_id_token: str

class GoogleLoginRequest(BaseModel):
    google_id_token: str

class UserRegistrationRequest(BaseModel):
    firebase_id_token: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    fcm_token: Optional[str] = None

class TokenVerifyRequest(BaseModel):
    token: str