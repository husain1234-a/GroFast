from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..firebase.auth import verify_firebase_token, verify_google_token
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import redis.asyncio as redis
import json
import logging
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from custom_logging import setup_logging

logger = setup_logging("auth-service", log_level="INFO")

# Redis client for session management
try:
    from ..config import settings
    redis_client = redis.from_url(settings.redis_url)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

class AuthService:
    @staticmethod
    async def create_or_get_user(db: AsyncSession, firebase_token: str) -> User:
        """Create or get user from Firebase token"""
        user_info: Dict[str, Any] = await verify_firebase_token(firebase_token)
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.firebase_uid == user_info["uid"])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user_data = UserCreate(
                firebase_uid=user_info["uid"],
                phone=user_info.get("phone"),
                email=user_info.get("email"),
                name=user_info.get("name"),
            )
            user = User(**user_data.model_dump())
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        for field, value in user_update.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def create_or_get_user_google(db: AsyncSession, google_token: str) -> User:
        """Create or get user from Google token"""
        user_info: Dict[str, Any] = await verify_google_token(google_token)
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.firebase_uid == user_info["uid"])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user from Google info
            user_data = UserCreate(
                firebase_uid=user_info["uid"],
                email=user_info.get("email"),
                name=user_info.get("name"),
            )
            user = User(**user_data.model_dump())
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> User:
        result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user_session(user_id: int, firebase_token: str, expires_in: int = 3600) -> str:
        """Create user session in Redis"""
        if not redis_client:
            return firebase_token  # Fallback to Firebase token
        
        try:
            session_key = f"session:{user_id}:{firebase_token[-8:]}"
            session_data = {
                "user_id": user_id,
                "firebase_token": firebase_token,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
            }
            
            await redis_client.setex(session_key, expires_in, json.dumps(session_data))
            logger.info(f"Session created for user {user_id}")
            return session_key
        
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return firebase_token  # Fallback
    
    @staticmethod
    async def validate_session(session_key: str) -> dict:
        """Validate user session"""
        if not redis_client:
            return None
        
        try:
            session_data = await redis_client.get(session_key)
            if session_data:
                data = json.loads(session_data)
                expires_at = datetime.fromisoformat(data["expires_at"])
                
                if datetime.utcnow() < expires_at:
                    return data
                else:
                    # Session expired, clean up
                    await redis_client.delete(session_key)
                    logger.info(f"Expired session cleaned up: {session_key}")
            
            return None
        
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    @staticmethod
    async def invalidate_session(session_key: str) -> bool:
        """Invalidate user session"""
        if not redis_client:
            return True  # No session to invalidate
        
        try:
            result = await redis_client.delete(session_key)
            logger.info(f"Session invalidated: {session_key}")
            return bool(result)
        
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return False
    
    @staticmethod
    async def get_users_count(db: AsyncSession) -> int:
        """Get total count of users"""
        result = await db.execute(select(func.count(User.id)))
        return result.scalar()
    
    @staticmethod
    async def get_users_list(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[User]:
        """Get paginated list of users"""
        result = await db.execute(
            select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
        )
        return result.scalars().all()