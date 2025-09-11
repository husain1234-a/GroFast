from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re

class UserBase(BaseModel):
    phone: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$', description="Valid phone number")
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User name")
    address: Optional[str] = Field(None, min_length=5, max_length=500, description="User address")
    latitude: Optional[str] = Field(None, regex=r'^-?([1-8]?\d(\.\d+)?|90(\.0+)?)$', description="Valid latitude")
    longitude: Optional[str] = Field(None, regex=r'^-?((1[0-7]|[1-9])?\d(\.\d+)?|180(\.0+)?)$', description="Valid longitude")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty')
            if not re.match(r'^[a-zA-Z\s\-\.\']+$', v):
                raise ValueError('Name contains invalid characters')
        return v
    
    @validator('address')
    def validate_address(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 5:
                raise ValueError('Address must be at least 5 characters long')
        return v

class UserCreate(UserBase):
    firebase_uid: str = Field(..., min_length=1, max_length=128, description="Firebase UID")
    fcm_token: Optional[str] = Field(None, max_length=255, description="FCM token")
    
    @validator('firebase_uid')
    def validate_firebase_uid(cls, v):
        if not v or not v.strip():
            raise ValueError('Firebase UID is required')
        return v.strip()

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    latitude: Optional[str] = Field(None, regex=r'^-?([1-8]?\d(\.\d+)?|90(\.0+)?)$')
    longitude: Optional[str] = Field(None, regex=r'^-?((1[0-7]|[1-9])?\d(\.\d+)?|180(\.0+)?)$')
    fcm_token: Optional[str] = Field(None, max_length=255)
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty')
            if not re.match(r'^[a-zA-Z\s\-\.\']+$', v):
                raise ValueError('Name contains invalid characters')
        return v

class UserResponse(UserBase):
    id: int
    firebase_uid: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    phone: str = Field(..., regex=r'^\+?[1-9]\d{1,14}$', description="Valid phone number")
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v or not v.strip():
            raise ValueError('Phone number is required')
        return v.strip()

class OTPVerifyRequest(BaseModel):
    firebase_id_token: str = Field(..., min_length=10, description="Firebase ID token")
    
    @validator('firebase_id_token')
    def validate_token(cls, v):
        if not v or not v.strip():
            raise ValueError('Firebase ID token is required')
        return v.strip()

class GoogleLoginRequest(BaseModel):
    google_id_token: str = Field(..., min_length=10, description="Google ID token")
    
    @validator('google_id_token')
    def validate_token(cls, v):
        if not v or not v.strip():
            raise ValueError('Google ID token is required')
        return v.strip()