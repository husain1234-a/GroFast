import sys
import os
import logging
from typing import List, Dict, Any
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared_config import BaseServiceSettings, ConfigurationError

logger = logging.getLogger(__name__)

class APIGatewaySettings(BaseServiceSettings):
    """API Gateway configuration with enhanced error handling"""
    
    # Services URLs
    auth_service_url: str = "http://localhost:8001"
    product_service_url: str = "http://localhost:8002"
    cart_service_url: str = "http://localhost:8003"
    order_service_url: str = "http://localhost:8004"
    delivery_service_url: str = "http://localhost:8005"
    notification_service_url: str = "http://localhost:8006"
    
    # Admin configuration
    admin_api_key: str = "admin123456789"
    
    # Gateway-specific settings
    request_timeout_seconds: int = 30
    max_retries: int = 3
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60
    rate_limit_requests_per_minute: int = 1000
    
    def get_service_name(self) -> str:
        return "api-gateway"
    
    def get_critical_vars(self) -> List[str]:
        """Critical variables required for API gateway to function"""
        base_vars = super().get_critical_vars()
        gateway_vars = [
            "auth_service_url",
            "product_service_url", 
            "cart_service_url",
            "order_service_url",
            "delivery_service_url",
            "notification_service_url",
            "admin_api_key"
        ]
        return base_vars + gateway_vars
    
    def get_optional_vars(self) -> List[str]:
        """Optional variables with graceful degradation"""
        base_vars = super().get_optional_vars()
        gateway_vars = [
            "request_timeout_seconds",
            "max_retries",
            "circuit_breaker_failure_threshold",
            "circuit_breaker_timeout_seconds",
            "rate_limit_requests_per_minute"
        ]
        return base_vars + gateway_vars
    
    def _post_init_validation(self):
        """Additional gateway-specific validation"""
        super()._post_init_validation()
        
        # Validate all service URLs
        service_urls = {
            "auth_service_url": self.auth_service_url,
            "product_service_url": self.product_service_url,
            "cart_service_url": self.cart_service_url,
            "order_service_url": self.order_service_url,
            "delivery_service_url": self.delivery_service_url,
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
        
        # Validate admin API key strength
        if len(self.admin_api_key) < 16:
            logger.warning("Admin API key is shorter than recommended 16 characters")
        
        # Validate timeout and retry settings
        if self.request_timeout_seconds < 5:
            logger.warning("Request timeout is less than 5 seconds, this may cause issues")
        elif self.request_timeout_seconds > 300:
            logger.warning("Request timeout is greater than 5 minutes, this may cause poor UX")
        
        if self.max_retries < 1:
            logger.warning("Max retries is less than 1, using default of 3")
            self.max_retries = 3
        elif self.max_retries > 10:
            logger.warning("Max retries is greater than 10, this may cause cascading failures")
        
        # Validate circuit breaker settings
        if self.circuit_breaker_failure_threshold < 3:
            logger.warning("Circuit breaker failure threshold is less than 3, may be too sensitive")
        
        if self.circuit_breaker_timeout_seconds < 30:
            logger.warning("Circuit breaker timeout is less than 30 seconds, may be too short")
        
        # Validate rate limiting
        if self.rate_limit_requests_per_minute < 100:
            logger.warning("Rate limit is less than 100 requests/minute, may be too restrictive")
    
    def get_gateway_configuration_health(self) -> Dict[str, Any]:
        """Get gateway-specific configuration health"""
        base_health = self.get_configuration_health()
        
        service_urls_health = {
            "auth_service": bool(self.auth_service_url),
            "product_service": bool(self.product_service_url),
            "cart_service": bool(self.cart_service_url),
            "order_service": bool(self.order_service_url),
            "delivery_service": bool(self.delivery_service_url),
            "notification_service": bool(self.notification_service_url)
        }
        
        gateway_health = {
            "service_urls_configured": service_urls_health,
            "admin_api_key_configured": bool(self.admin_api_key),
            "timeout_settings": {
                "request_timeout_seconds": self.request_timeout_seconds,
                "circuit_breaker_timeout_seconds": self.circuit_breaker_timeout_seconds
            },
            "resilience_settings": {
                "max_retries": self.max_retries,
                "circuit_breaker_failure_threshold": self.circuit_breaker_failure_threshold,
                "rate_limit_requests_per_minute": self.rate_limit_requests_per_minute
            }
        }
        
        base_health["gateway_specific"] = gateway_health
        return base_health
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get all configured service URLs for HTTP client initialization"""
        return {
            "auth-service": self.auth_service_url,
            "product-service": self.product_service_url,
            "cart-service": self.cart_service_url,
            "order-service": self.order_service_url,
            "delivery-service": self.delivery_service_url,
            "notification-service": self.notification_service_url
        }

# Create settings instance with error handling
try:
    settings = APIGatewaySettings()
    logger.info("API Gateway configuration loaded successfully")
except ConfigurationError as e:
    logger.critical(f"API Gateway configuration failed: {e}")
    # In production, you might want to exit here
    # import sys
    # sys.exit(1)
    raise
except Exception as e:
    logger.critical(f"Unexpected error loading API Gateway configuration: {e}")
    raise