from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..firebase.auth import verify_firebase_token, verify_google_token
from fastapi import HTTPException, status

class AuthService:
    @staticmethod
    async def create_or_get_user(db: AsyncSession, firebase_token: str) -> User:
        # Verify Firebase token and get user info
        try:
            user_info = verify_firebase_token(firebase_token)
        except HTTPException:
            # Re-raise HTTP exceptions (invalid token, etc.)
            raise
        except Exception as e:
            # Handle other errors
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
        
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
        # Verify Google token via Firebase and get user info
        try:
            user_info = verify_google_token(google_token)
        except HTTPException:
            # Re-raise HTTP exceptions (invalid token, etc.)
            raise
        except Exception as e:
            # Handle other errors
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token verification failed"
            )
        
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