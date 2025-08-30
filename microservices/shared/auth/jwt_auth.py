from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-jwt-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

class JWTAuth:
    """Enhanced JWT authentication with proper validation"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
        """Extract user ID from JWT token"""
        payload = JWTAuth.verify_token(credentials.credentials)
        return int(payload.get("sub"))
    
    @staticmethod
    def create_user_token(user_id: int, email: str = None) -> str:
        """Create token for user authentication"""
        token_data = {
            "sub": str(user_id),
            "email": email,
            "type": "access"
        }
        return JWTAuth.create_access_token(token_data)

# Dependency for protected routes
async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Dependency to get current authenticated user ID"""
    return JWTAuth.get_current_user_id(credentials)

# Optional authentication (for routes that work with or without auth)
async def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[int]:
    """Optional authentication dependency"""
    if not credentials:
        return None
    try:
        return JWTAuth.get_current_user_id(credentials)
    except HTTPException:
        return None