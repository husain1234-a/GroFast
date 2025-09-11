from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..firebase.auth import verify_firebase_token, verify_google_token
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import redis
import json
import logging

logger = logging.getLogger(__name__)

# Redis client for session management
try:
    from ..config.settings import settings
    redis_client = redis.from_url(settings.redis_url)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

class AuthService:
    @staticmethod
    async def create_or_get_user(
        db: AsyncSession, 
        firebase_token: str
    ) -> User:
        """Create or get user from Firebase token"""
        user_info: Dict[str, Any] = await verify_firebase_token(firebase_token)
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.firebase_uid == user_info['uid'])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user_data = UserCreate(
                firebase_uid=user_info['uid'],
                phone=user_info.get('phone'),
                email=user_info.get('email'),
                name=user_info.get('name')
            )
            user = User(**user_data.model_dump())
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user
    
    @staticmethod
    async def update_user(
        db: AsyncSession, 
        user_id: int, 
        user_update: UserUpdate
    ) -> User:
        """Update user information"""
        result = await db.execute(select(User).where(User.id == user_id))
        user: Optional[User] = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        for field, value in user_update.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def create_or_get_user_google(
        db: AsyncSession, 
        google_token: str
    ) -> User:
        """Create or get user from Google token"""
        user_info: Dict[str, Any] = await verify_google_token(google_token)
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.firebase_uid == user_info['uid'])
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user from Google info
            user_data = UserCreate(
                firebase_uid=user_info['uid'],
                email=user_info.get('email'),
                name=user_info.get('name')
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
                "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
            }
            
            redis_client.setex(session_key, expires_in, json.dumps(session_data))
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
            session_data = redis_client.get(session_key)
            if session_data:
                data = json.loads(session_data)
                expires_at = datetime.fromisoformat(data["expires_at"])
                
                if datetime.utcnow() < expires_at:
                    return data
                else:
                    # Session expired, clean up
                    redis_client.delete(session_key)
                    logger.info(f"Expired session cleaned up: {session_key}")
            
            return None
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    @staticmethod
    async def refresh_session(session_key: str, expires_in: int = 3600) -> bool:
        """Refresh user session"""
        if not redis_client:
            return False
        
        try:
            session_data = await AuthService.validate_session(session_key)
            if session_data:
                # Update expiry
                session_data["expires_at"] = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
                redis_client.setex(session_key, expires_in, json.dumps(session_data))
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Session refresh error: {e}")
            return False
    
    @staticmethod
    async def invalidate_session(session_key: str) -> bool:
        """Invalidate user session"""
        if not redis_client:
            return True  # No session to invalidate
        
        try:
            result = redis_client.delete(session_key)
            logger.info(f"Session invalidated: {session_key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return False
    
    @staticmethod
    async def get_user_sessions(user_id: int) -> list:
        """Get all active sessions for a user"""
        if not redis_client:
            return []
        
        try:
            pattern = f"session:{user_id}:*"
            session_keys = redis_client.keys(pattern)
            
            sessions = []
            for key in session_keys:
                session_data = await AuthService.validate_session(key.decode())
                if session_data:
                    sessions.append({
                        "session_key": key.decode(),
                        "created_at": session_data["created_at"],
                        "expires_at": session_data["expires_at"]
                    })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    @staticmethod
    async def invalidate_all_user_sessions(user_id: int) -> int:
        """Invalidate all sessions for a user"""
        if not redis_client:
            return 0
        
        try:
            pattern = f"session:{user_id}:*"
            session_keys = redis_client.keys(pattern)
            
            if session_keys:
                count = redis_client.delete(*session_keys)
                logger.info(f"Invalidated {count} sessions for user {user_id}")
                return count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating user sessions: {e}")
            return 0
