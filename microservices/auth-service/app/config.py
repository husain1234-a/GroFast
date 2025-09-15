import sys
import os
import logging
from typing import List, Dict, Any, Optional
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared_config import BaseServiceSettings, ConfigurationError

logger = logging.getLogger(__name__)

class AuthServiceSettings(BaseServiceSettings):
    """Auth service configuration with enhanced error handling"""
    
    # Firebase configuration (optional for demo mode)
    firebase_credentials_path: Optional[str] = None
    firebase_project_id: Optional[str] = None
    
    # Google OAuth configuration (optional for demo mode)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # Optional auth-specific settings
    token_expiry_hours: int = 24
    refresh_token_expiry_days: int = 30
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    def get_service_name(self) -> str:
        return "auth-service"
    
    def get_critical_vars(self) -> List[str]:
        """Critical variables required for auth service to function"""
        base_vars = super().get_critical_vars()
        # Firebase vars are optional for demo mode
        return base_vars
    
    def get_optional_vars(self) -> List[str]:
        """Optional variables with graceful degradation"""
        base_vars = super().get_optional_vars()
        auth_vars = [
            "firebase_credentials_path",
            "firebase_project_id", 
            "google_client_id",
            "google_client_secret",
            "token_expiry_hours",
            "refresh_token_expiry_days",
            "max_login_attempts",
            "lockout_duration_minutes"
        ]
        return base_vars + auth_vars
    
    def _post_init_validation(self):
        """Additional auth-specific validation"""
        super()._post_init_validation()
        
        # Validate Firebase credentials file exists (if provided)
        if self.firebase_credentials_path and not os.path.exists(self.firebase_credentials_path):
            logger.warning(f"Firebase credentials file not found: {self.firebase_credentials_path}")
            # Don't fail startup, but log warning for monitoring
        elif not self.firebase_credentials_path:
            logger.info("No Firebase credentials path provided - running in demo mode")
        
        # Validate token expiry settings
        if self.token_expiry_hours < 1:
            logger.warning("Token expiry hours is less than 1, using default of 24")
            self.token_expiry_hours = 24
        
        if self.refresh_token_expiry_days < 1:
            logger.warning("Refresh token expiry days is less than 1, using default of 30")
            self.refresh_token_expiry_days = 30
        
        # Validate security settings
        if self.max_login_attempts < 3:
            logger.warning("Max login attempts is less than 3, using default of 5")
            self.max_login_attempts = 5
    
    def get_auth_configuration_health(self) -> Dict[str, Any]:
        """Get auth-specific configuration health"""
        base_health = self.get_configuration_health()
        
        auth_health = {
            "firebase_credentials_file_exists": bool(self.firebase_credentials_path and os.path.exists(self.firebase_credentials_path)),
            "demo_mode": not bool(self.firebase_credentials_path),
            "token_expiry_hours": self.token_expiry_hours,
            "refresh_token_expiry_days": self.refresh_token_expiry_days,
            "security_settings": {
                "max_login_attempts": self.max_login_attempts,
                "lockout_duration_minutes": self.lockout_duration_minutes
            }
        }
        
        base_health["auth_specific"] = auth_health
        return base_health

# Create settings instance with error handling
try:
    settings = AuthServiceSettings()
    logger.info("Auth service configuration loaded successfully")
except ConfigurationError as e:
    logger.critical(f"Auth service configuration failed: {e}")
    # In production, you might want to exit here
    # import sys
    # sys.exit(1)
    raise
except Exception as e:
    logger.critical(f"Unexpected error loading auth service configuration: {e}")
    raise