from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Services URLs
    auth_service_url: str = "http://localhost:8001"
    product_service_url: str = "http://localhost:8002"
    cart_service_url: str = "http://localhost:8003"
    order_service_url: str = "http://localhost:8004"
    delivery_service_url: str = "http://localhost:8005"
    notification_service_url: str = "http://localhost:8006"
    
    # Redis for rate limiting
    redis_url: str = "redis://localhost:6379/0"
    
    # App Settings
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"

settings = Settings()