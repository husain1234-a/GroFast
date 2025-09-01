import sys
import os
import logging
from typing import List, Dict, Any
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared_config import BaseServiceSettings, ConfigurationError

logger = logging.getLogger(__name__)

class DeliveryServiceSettings(BaseServiceSettings):
    """Delivery service configuration with enhanced error handling"""
    
    # Supabase configuration
    supabase_url: str
    supabase_key: str
    
    # Delivery-specific settings
    delivery_radius_km: float = 50.0
    max_delivery_time_hours: int = 24
    delivery_fee_base: float = 5.0
    delivery_tracking_update_interval_seconds: int = 60
    
    def get_service_name(self) -> str:
        return "delivery-service"
    
    def get_critical_vars(self) -> List[str]:
        """Critical variables required for delivery service to function"""
        base_vars = super().get_critical_vars()
        delivery_vars = [
            "supabase_url",
            "supabase_key"
        ]
        return base_vars + delivery_vars
    
    def get_optional_vars(self) -> List[str]:
        """Optional variables with graceful degradation"""
        base_vars = super().get_optional_vars()
        delivery_vars = [
            "delivery_radius_km",
            "max_delivery_time_hours",
            "delivery_fee_base",
            "delivery_tracking_update_interval_seconds"
        ]
        return base_vars + delivery_vars
    
    def _post_init_validation(self):
        """Additional delivery-specific validation"""
        super()._post_init_validation()
        
        # Validate Supabase URL
        if not self.supabase_url.startswith(('http://', 'https://')):
            raise ConfigurationError(
                f"Invalid Supabase URL format: {self.supabase_url}",
                invalid_vars={"supabase_url": "Must be a valid HTTP/HTTPS URL"}
            )
        
        # Validate Supabase key
        if len(self.supabase_key) < 32:
            logger.warning("Supabase key appears to be shorter than expected")
        
        # Validate delivery settings
        if self.delivery_radius_km <= 0:
            logger.warning("Delivery radius is 0 or negative, using default of 50km")
            self.delivery_radius_km = 50.0
        elif self.delivery_radius_km > 500:
            logger.warning("Delivery radius is greater than 500km, this may be unrealistic")
        
        if self.max_delivery_time_hours < 1:
            logger.warning("Max delivery time is less than 1 hour, using default of 24")
            self.max_delivery_time_hours = 24
        elif self.max_delivery_time_hours > 168:  # 1 week
            logger.warning("Max delivery time is greater than 1 week, this may cause customer issues")
        
        if self.delivery_fee_base < 0:
            logger.warning("Delivery fee base is negative, using default of 5.0")
            self.delivery_fee_base = 5.0
        
        if self.delivery_tracking_update_interval_seconds < 30:
            logger.warning("Delivery tracking update interval is less than 30 seconds, may cause performance issues")

# Create settings instance with error handling
try:
    settings = DeliveryServiceSettings()
    logger.info("Delivery service configuration loaded successfully")
except ConfigurationError as e:
    logger.critical(f"Delivery service configuration failed: {e}")
    raise
except Exception as e:
    logger.critical(f"Unexpected error loading delivery service configuration: {e}")
    raise