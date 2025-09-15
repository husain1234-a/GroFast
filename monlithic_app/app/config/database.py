from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .settings import settings

# Create async engine with optimized configuration
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Disable SQL logging for performance
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,  # Reduced pool size
    max_overflow=10,  # Reduced overflow
    connect_args={
        "server_settings": {
            "application_name": "blinkit_clone"
        },
        "command_timeout": 5,  # 5 second timeout
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()