from pydantic_settings import BaseSettings
from typing import List

class ProductServiceSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:admin123@localhost:5432/grofast_db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "super-secret-jwt-key"
    jwt_algorithm: str = "HS256"
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_master_key: str = "dummy-master-key-123"
    r2_endpoint_url: str = "https://dummy-account.r2.cloudflarestorage.com"
    r2_access_key_id: str = "dummy_access_key_123"
    r2_secret_access_key: str = "dummy_secret_key_456"
    r2_bucket_name: str = "grofast-assets"
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080", "https://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = ProductServiceSettings()