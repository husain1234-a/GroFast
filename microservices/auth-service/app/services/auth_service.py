from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from fastapi import HTTPException, status

class AuthService:
    @staticmethod
    async def create_or_get_user(db: AsyncSession, firebase_token: str) -> User:
        # Simple token validation - in production use Firebase SDK
        if not firebase_token or len(firebase_token) < 10:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Extract mock UID from token (last 8 chars)
        mock_uid = f"firebase_{firebase_token[-8:]}"
        
        result = await db.execute(select(User).where(User.firebase_uid == mock_uid))
        user = result.scalar_one_or_none()
        
        if not user:
            user_data = UserCreate(
                firebase_uid=mock_uid,
                email="demo@example.com",
                name="Demo User"
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
        # Simple Google token validation
        return await AuthService.create_or_get_user(db, google_token)
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def invalidate_session(session_key: str):
        # Mock session invalidation
        pass
    
    @staticmethod
    async def create_user_session(user_id: int, firebase_token: str) -> str:
        # Mock session creation
        return f"session:{user_id}:{firebase_token[-8:]}"