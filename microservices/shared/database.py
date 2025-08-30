from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
            connect_args={
                "server_settings": {
                    "application_name": "blinkit_microservice"
                }
            }
        )
        self.AsyncSessionLocal = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_db(self):
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()