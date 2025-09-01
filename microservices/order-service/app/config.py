import sys
import os
import logging
from typing import List, Dict, Any
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared_config import BaseServiceSettings, ConfigurationError

logger = logging.getLogger(__name__)

class OrderServiceSettings(BaseServiceSettings):
    """Order service configuration with enhanced error handling"""
    
    # External service URLs
    cart_service_url: str = "http://localhost:8003"
    notification_service_url: str = "http://localhost:8006"
    
    # Order-specific settings
    order_timeout_minutes: int = 30
    max_order_value: float = 10000.0
    order_status_update_interval_seconds: int = 30
    payment_timeout_minutes: int = 15
    
    def get_service_name(self) -> str:
        return "order-service"
    
    def get_critical_vars(self) -> List[str]:
        """Critical variables required for order service to function"""
        base_vars = super().get_critical_vars()
        order_vars = [
            "cart_service_url",
            "notification_service_url"
        ]
        return base_vars + order_vars
    
    def get_optional_vars(self) -> List[str]:
        """Optional variables with graceful degradation"""
        base_vars = super().get_optional_vars()
        order_vars = [
            "order_timeout_minutes",
            "max_order_value",
            "order_status_update_interval_seconds",
            "payment_timeout_minutes"
        ]
        return base_vars + order_vars
    
    def _post_init_validation(self):
        """Additional order-specific validation"""
        super()._post_init_validation()
        
        # Validate service URLs
        service_urls = {
            "cart_service_url": self.cart_service_url,
            "notification_service_url": self.notification_service_url
        }
        
        invalid_urls = {}
        for name, url in service_urls.items():
            if not url.startswith(('http://', 'https://')):
                invalid_urls[name] = "Must be a valid HTTP/HTTPS URL"
        
        if invalid_urls:
            raise ConfigurationError(
                "Invalid service URL configurations",
                invalid_vars=invalid_urls
            )
        
        # Validate order settings
        if self.order_timeout_minutes < 5:
            logger.warning("Order timeout is less than 5 minutes, using default of 30")
            self.order_timeout_minutes = 30
        elif self.order_timeout_minutes > 1440:  # 24 hours
            logger.warning("Order timeout is greater than 24 hours, this may cause issues")
        
        if self.max_order_value <= 0:
            logger.warning("Max order value is 0 or negative, using default of 10000")
            self.max_order_value = 10000.0
        
        if self.order_status_update_interval_seconds < 10:
            logger.warning("Order status update interval is less than 10 seconds, may cause performance issues")
        
        if self.payment_timeout_minutes < 5:
            logger.warning("Payment timeout is less than 5 minutes, using default of 15")
            self.payment_timeout_minutes = 15
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get all configured service URLs for HTTP client initialization"""
        return {
            "cart-service": self.cart_service_url,
            "notification-service": self.notification_service_url
        }

# Create settings instance with error handling
try:
    settings = OrderServiceSettings()
    logger.info("Order service configuration loaded successfully")
except ConfigurationError as e:
    logger.critical(f"Order service configuration failed: {e}")
    raise
except Exception as e:
    logger.critical(f"Unexpected error loading order service configuration: {e}")
    raise