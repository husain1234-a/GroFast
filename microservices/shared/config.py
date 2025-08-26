from pydantic_settings import BaseSettings
from typing import List

class BaseServiceSettings(BaseSettings):
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    
    # App Settings
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

class AuthServiceSettings(BaseServiceSettings):
    # Firebase
    firebase_credentials_path: str
    firebase_project_id: str
    google_client_id: str
    google_client_secret: str

class NotificationServiceSettings(BaseServiceSettings):
    # Notifications
    fcm_server_key: str
    resend_api_key: str
    textbelt_api_key: str

class DeliveryServiceSettings(BaseServiceSettings):
    # Supabase
    supabase_url: str
    supabase_key: str

class ProductServiceSettings(BaseServiceSettings):
    # Meilisearch
    meilisearch_url: str
    meilisearch_master_key: str
    
    # Cloudflare R2
    r2_endpoint_url: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str