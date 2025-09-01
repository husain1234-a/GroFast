import sys
import os
import logging
from typing import List, Dict, Any
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared_config import BaseServiceSettings, ConfigurationError

logger = logging.getLogger(__name__)

class CartServiceSettings(BaseServiceSettings):
    """Cart service configuration with enhanced error handling"""
    
    # External service URLs
    product_service_url: str = "http://localhost:8002"
    
    # Cart-specific settings
    cart_expiry_days: int = 30
    max_items_per_cart: int = 100
    cart_cleanup_interval_hours: int = 24
    
    def get_service_name(self) -> str:
        return "cart-service"
    
    def get_critical_vars(self) -> List[str]:
        """Critical variables required for cart service to function"""
        base_vars = super().get_critical_vars()
        cart_vars = ["product_service_url"]
        return base_vars + cart_vars
    
    def get_optional_vars(self) -> List[str]:
        """Optional variables with graceful degradation"""
        base_vars = super().get_optional_vars()
        cart_vars = [
            "cart_expiry_days",
            "max_items_per_cart", 
            "cart_cleanup_interval_hours"
        ]
        return base_vars + cart_vars
    
    def _post_init_validation(self):
        """Additional cart-specific validation"""
        super()._post_init_validation()
        
        # Validate product service URL
        if not self.product_service_url.startswith(('http://', 'https://')):
            raise ConfigurationError(
                f"Invalid product service URL format: {self.product_service_url}",
                invalid_vars={"product_service_url": "Must be a valid HTTP/HTTPS URL"}
            )
        
        # Validate cart settings
        if self.cart_expiry_days < 1:
            logger.warning("Cart expiry days is less than 1, using default of 30")
            self.cart_expiry_days = 30
        elif self.cart_expiry_days > 365:
            logger.warning("Cart expiry days is greater than 365, this may cause storage issues")
        
        if self.max_items_per_cart < 1:
            logger.warning("Max items per cart is less than 1, using default of 100")
            self.max_items_per_cart = 100
        elif self.max_items_per_cart > 1000:
            logger.warning("Max items per cart is greater than 1000, this may cause performance issues")
        
        if self.cart_cleanup_interval_hours < 1:
            logger.warning("Cart cleanup interval is less than 1 hour, using default of 24")
            self.cart_cleanup_interval_hours = 24
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get all configured service URLs for HTTP client initialization"""
        return {
            "product-service": self.product_service_url
        }

# Create settings instance with error handling
try:
    settings = CartServiceSettings()
    logger.info("Cart service configuration loaded successfully")
except ConfigurationError as e:
    logger.critical(f"Cart service configuration failed: {e}")
    raise
except Exception as e:
    logger.critical(f"Unexpected error loading cart service configuration: {e}")
    raise