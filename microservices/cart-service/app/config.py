from pydantic_settings import BaseSettings
from typing import List

class CartServiceSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:admin123@localhost:5432/grofast_db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "super-secret-jwt-key"
    jwt_algorithm: str = "HS256"
    product_service_url: str = "http://localhost:8002"
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080", "https://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = CartServiceSettings()