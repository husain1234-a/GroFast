from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
# from ..firebase.auth import verify_firebase_token, verify_google_token
from fastapi import HTTPException, status

class AuthService:
    @staticmethod
    async def create_or_get_user(db: AsyncSession, firebase_token: str) -> User:
        # Demo implementation
        firebase_uid = f"user_{firebase_token[-8:]}"
        user_info = {
            'uid': firebase_uid,
            'email': f"user{firebase_uid[-4:]}@example.com",
            'name': f"User {firebase_uid[-4:]}",
            'phone': None
        }
        
        result = await db.execute(select(User).where(User.firebase_uid == user_info['uid']))
        user = result.scalar_one_or_none()
        
        if not user:
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
        # Demo implementation
        firebase_uid = f"google_{google_token[-8:]}"
        user_info = {
            'uid': firebase_uid,
            'email': f"google{firebase_uid[-4:]}@example.com",
            'name': f"Google User {firebase_uid[-4:]}"
        }
        
        result = await db.execute(select(User).where(User.firebase_uid == user_info['uid']))
        user = result.scalar_one_or_none()
        
        if not user:
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
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            for field, value in user_update.model_dump(exclude_unset=True).items():
                setattr(user, field, value)
            await db.commit()
            await db.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()