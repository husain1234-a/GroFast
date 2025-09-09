import sys
import os
import logging
from typing import List, Dict, Any
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared_config import BaseServiceSettings, ConfigurationError

logger = logging.getLogger(__name__)

class NotificationServiceSettings(BaseServiceSettings):
    """Notification service configuration with enhanced error handling"""
    
    # External service keys (Firebase Admin SDK replaces FCM server key)
    firebase_credentials_path: str
    resend_api_key: str
    
    # Notification-specific settings
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 5
    notification_batch_size: int = 100
    email_rate_limit_per_hour: int = 1000
    push_rate_limit_per_hour: int = 5000
    
    def get_service_name(self) -> str:
        return "notification-service"
    
    def get_critical_vars(self) -> List[str]:
        """Critical variables required for notification service to function"""
        base_vars = super().get_critical_vars()
        notification_vars = [
            "firebase_credentials_path",
            "resend_api_key"
        ]
        return base_vars + notification_vars
    
    def get_optional_vars(self) -> List[str]:
        """Optional variables with graceful degradation"""
        base_vars = super().get_optional_vars()
        notification_vars = [
            "max_retry_attempts",
            "retry_delay_seconds",
            "notification_batch_size",
            "email_rate_limit_per_hour",
            "push_rate_limit_per_hour"
        ]
        return base_vars + notification_vars
    
    def _post_init_validation(self):
        """Additional notification-specific validation"""
        super()._post_init_validation()
        
        # Validate Firebase credentials file exists
        if not os.path.exists(self.firebase_credentials_path):
            logger.warning(f"Firebase credentials file not found: {self.firebase_credentials_path}")
        else:
            logger.info("Firebase credentials file found - using Firebase Admin SDK")
        
        # Validate Resend API key format
        if not self.resend_api_key.startswith('re_'):
            logger.warning("Resend API key format may be invalid (should start with 're_')")
        
        # Validate retry settings
        if self.max_retry_attempts < 1:
            logger.warning("Max retry attempts is less than 1, using default of 3")
            self.max_retry_attempts = 3
        elif self.max_retry_attempts > 10:
            logger.warning("Max retry attempts is greater than 10, this may cause delays")
        
        if self.retry_delay_seconds < 1:
            logger.warning("Retry delay is less than 1 second, using default of 5")
            self.retry_delay_seconds = 5
        elif self.retry_delay_seconds > 300:
            logger.warning("Retry delay is greater than 5 minutes, this may cause long delays")
        
        # Validate batch and rate limit settings
        if self.notification_batch_size < 1:
            logger.warning("Notification batch size is less than 1, using default of 100")
            self.notification_batch_size = 100
        elif self.notification_batch_size > 1000:
            logger.warning("Notification batch size is greater than 1000, may cause memory issues")
        
        if self.email_rate_limit_per_hour < 100:
            logger.warning("Email rate limit is less than 100/hour, may be too restrictive")
        
        if self.push_rate_limit_per_hour < 1000:
            logger.warning("Push notification rate limit is less than 1000/hour, may be too restrictive")

# Create settings instance with error handling
try:
    settings = NotificationServiceSettings()
    logger.info("Notification service configuration loaded successfully")
except ConfigurationError as e:
    logger.critical(f"Notification service configuration failed: {e}")
    raise
except Exception as e:
    logger.critical(f"Unexpected error loading notification service configuration: {e}")
    raise