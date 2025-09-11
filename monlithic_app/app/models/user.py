from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from ..config.database import Base

class User(Base):
    """User model for storing user information and authentication data."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(128), unique=True, index=True, nullable=False)
    phone = Column(String(15), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(100))
    fcm_token = Column(Text)  # For push notifications
    address = Column(Text)
    latitude = Column(String(20))
    longitude = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())