from pydantic_settings import BaseSettings
from typing import List

class NotificationServiceSettings(BaseSettings):
    fcm_server_key: str = "AAAA1234567890:APA91bHdummy_fcm_server_key_for_development"
    resend_api_key: str = ""
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080", "https://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = NotificationServiceSettings()