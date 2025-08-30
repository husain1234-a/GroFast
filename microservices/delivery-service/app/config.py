from pydantic_settings import BaseSettings
from typing import List

class DeliveryServiceSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:admin123@localhost:5432/grofast_db"
    redis_url: str = "redis://localhost:6379/0"
    supabase_url: str = "https://ktpugnrihesretpdzbkn.supabase.co"
    supabase_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt0cHVnbnJpaGVzcmV0cGR6YmtuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE3ODYzODAsImV4cCI6MjA2NzM2MjM4MH0.ZLhDDC8b_JUfTvt6yPxl8yk8l4F9DDHNTEWIaBVfQ84"
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080", "https://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = DeliveryServiceSettings()