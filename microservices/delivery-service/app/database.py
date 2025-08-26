from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from pydantic_settings import BaseSettings
from typing import List

class DeliveryServiceSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password123@localhost:5432/blinkit_db"
    redis_url: str = "redis://localhost:6379/0"
    supabase_url: str = "https://ktpugnrihesretpdzbkn.supabase.co"
    supabase_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt0cHVnbnJpaGVzcmV0cGR6YmtuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE3ODYzODAsImV4cCI6MjA2NzM2MjM4MH0.ZLhDDC8b_JUfTvt6yPxl8yk8l4F9DDHNTEWIaBVfQ84"
    
    class Config:
        env_file = ".env"

settings = DeliveryServiceSettings()

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