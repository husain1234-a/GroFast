from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password123@localhost:5432/blinkit_db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "super-secret-jwt-key"
    jwt_algorithm: str = "HS256"
    debug: bool = True
    cors_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()

engine = create_async_engine(
    "postgresql+asyncpg://postgres:admin123@localhost:5432/grofast_db",
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()