from pydantic_settings import BaseSettings
from typing import List

class NotificationServiceSettings(BaseSettings):
    fcm_server_key: str = "AAAA1234567890:APA91bHdummy_fcm_server_key_for_development"
    resend_api_key: str = ""
    debug: bool = True
    cors_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"

settings = NotificationServiceSettings()