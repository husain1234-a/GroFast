import sys
import os
import logging
from typing import List, Dict, Any
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from shared_config import BaseServiceSettings, ConfigurationError

logger = logging.getLogger(__name__)

class ProductServiceSettings(BaseServiceSettings):
    """Product service configuration with enhanced error handling"""
    
    # Meilisearch configuration
    meilisearch_url: str
    meilisearch_master_key: str
    
    # R2/S3 storage configuration
    r2_endpoint_url: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str
    
    # Optional product-specific settings
    max_image_size_mb: int = 10
    allowed_image_types: List[str] = ["image/jpeg", "image/png", "image/webp"]
    search_results_per_page: int = 20
    max_search_results: int = 1000
    
    def get_service_name(self) -> str:
        return "product-service"
    
    def get_critical_vars(self) -> List[str]:
        """Critical variables required for product service to function"""
        base_vars = super().get_critical_vars()
        product_vars = [
            "meilisearch_url",
            "meilisearch_master_key",
            "r2_endpoint_url",
            "r2_access_key_id", 
            "r2_secret_access_key",
            "r2_bucket_name"
        ]
        return base_vars + product_vars
    
    def get_optional_vars(self) -> List[str]:
        """Optional variables with graceful degradation"""
        base_vars = super().get_optional_vars()
        product_vars = [
            "max_image_size_mb",
            "allowed_image_types",
            "search_results_per_page",
            "max_search_results"
        ]
        return base_vars + product_vars
    
    def _post_init_validation(self):
        """Additional product-specific validation"""
        super()._post_init_validation()
        
        # Validate Meilisearch URL format
        if not self.meilisearch_url.startswith(('http://', 'https://')):
            raise ConfigurationError(
                f"Invalid Meilisearch URL format: {self.meilisearch_url}",
                invalid_vars={"meilisearch_url": "Must be a valid HTTP/HTTPS URL"}
            )
        
        # Validate R2 endpoint URL format
        if not self.r2_endpoint_url.startswith(('http://', 'https://')):
            raise ConfigurationError(
                f"Invalid R2 endpoint URL format: {self.r2_endpoint_url}",
                invalid_vars={"r2_endpoint_url": "Must be a valid HTTP/HTTPS URL"}
            )
        
        # Validate image size limits
        if self.max_image_size_mb < 1:
            logger.warning("Max image size is less than 1MB, using default of 10MB")
            self.max_image_size_mb = 10
        elif self.max_image_size_mb > 50:
            logger.warning("Max image size is greater than 50MB, this may cause performance issues")
        
        # Validate search pagination settings
        if self.search_results_per_page < 1:
            logger.warning("Search results per page is less than 1, using default of 20")
            self.search_results_per_page = 20
        elif self.search_results_per_page > 100:
            logger.warning("Search results per page is greater than 100, this may cause performance issues")
        
        if self.max_search_results < self.search_results_per_page:
            logger.warning("Max search results is less than results per page, adjusting")
            self.max_search_results = self.search_results_per_page * 10
    
    def get_product_configuration_health(self) -> Dict[str, Any]:
        """Get product-specific configuration health"""
        base_health = self.get_configuration_health()
        
        product_health = {
            "meilisearch_configured": bool(self.meilisearch_url and self.meilisearch_master_key),
            "r2_storage_configured": bool(all([
                self.r2_endpoint_url, self.r2_access_key_id, 
                self.r2_secret_access_key, self.r2_bucket_name
            ])),
            "image_settings": {
                "max_size_mb": self.max_image_size_mb,
                "allowed_types_count": len(self.allowed_image_types)
            },
            "search_settings": {
                "results_per_page": self.search_results_per_page,
                "max_results": self.max_search_results
            }
        }
        
        base_health["product_specific"] = product_health
        return base_health

# Create settings instance with error handling
try:
    settings = ProductServiceSettings()
    logger.info("Product service configuration loaded successfully")
except ConfigurationError as e:
    logger.critical(f"Product service configuration failed: {e}")
    # In production, you might want to exit here
    # import sys
    # sys.exit(1)
    raise
except Exception as e:
    logger.critical(f"Unexpected error loading product service configuration: {e}")
    raise