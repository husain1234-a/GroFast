from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # Firebase
    firebase_credentials_path: str
    firebase_project_id: str
    
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # Cloudflare R2
    r2_endpoint_url: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str
    
    # Meilisearch
    meilisearch_url: str
    meilisearch_master_key: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    
    # App
    app_name: str = "Blinkit Clone"
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Notifications
    fcm_server_key: str
    resend_api_key: str
    textbelt_api_key: str = "textbelt"
    
    class Config:
        env_file = ".env"

settings = Settings()