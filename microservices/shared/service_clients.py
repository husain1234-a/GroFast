"""
Service client factory and management utilities
Provides standardized HTTP clients for inter-service communication
"""

import logging
from typing import Dict, Optional, Any
from http_client import ResilientHttpClient, create_service_client, ServiceError
import asyncio

logger = logging.getLogger(__name__)

class ServiceClientManager:
    """Manages HTTP clients for all external services"""
    
    def __init__(self):
        self._clients: Dict[str, ResilientHttpClient] = {}
        self._service_urls: Dict[str, str] = {}
        self._initialized = False
    
    def initialize(self, service_urls: Dict[str, str], **client_kwargs):
        """Initialize all service clients"""
        self._service_urls = service_urls.copy()
        
        for service_name, base_url in service_urls.items():
            if not base_url:
                logger.warning(f"No URL configured for service: {service_name}")
                continue
            
            try:
                client = create_service_client(
                    service_name=service_name,
                    base_url=base_url,
                    **client_kwargs
                )
                self._clients[service_name] = client
                logger.info(f"Initialized HTTP client for {service_name} at {base_url}")
                
            except Exception as e:
                logger.error(f"Failed to initialize client for {service_name}: {e}")
        
        self._initialized = True
        logger.info(f"Service client manager initialized with {len(self._clients)} clients")
    
    def get_client(self, service_name: str) -> Optional[ResilientHttpClient]:
        """Get HTTP client for a specific service"""
        if not self._initialized:
            logger.error("Service client manager not initialized")
            return None
        
        client = self._clients.get(service_name)
        if not client:
            logger.error(f"No client configured for service: {service_name}")
        
        return client
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health checks on all configured services"""
        if not self._initialized:
            return {"error": "Service client manager not initialized"}
        
        health_results = {}
        
        # Run health checks concurrently
        tasks = []
        for service_name, client in self._clients.items():
            task = asyncio.create_task(
                client.health_check(),
                name=f"health_check_{service_name}"
            )
            tasks.append((service_name, task))
        
        # Collect results
        for service_name, task in tasks:
            try:
                result = await task
                health_results[service_name] = result
            except Exception as e:
                health_results[service_name] = {
                    "service": service_name,
                    "status": "error",
                    "error": str(e)
                }
        
        # Calculate overall health
        healthy_services = sum(1 for result in health_results.values() 
                             if result.get("status") == "healthy")
        total_services = len(health_results)
        
        overall_status = "healthy" if healthy_services == total_services else "degraded"
        if healthy_services == 0:
            overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "healthy_services": healthy_services,
            "total_services": total_services,
            "services": health_results
        }
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get statistics for all clients"""
        if not self._initialized:
            return {"error": "Service client manager not initialized"}
        
        stats = {}
        for service_name, client in self._clients.items():
            stats[service_name] = client.get_client_stats()
        
        return stats
    
    def list_services(self) -> Dict[str, str]:
        """List all configured services and their URLs"""
        return self._service_urls.copy()

# Global service client manager instance
service_client_manager = ServiceClientManager()

# Convenience functions for common service operations
async def call_auth_service(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Call auth service with error handling"""
    client = service_client_manager.get_client("auth-service")
    if not client:
        raise ServiceError("Auth service client not available", service_name="auth-service")
    
    try:
        if method.upper() == "GET":
            return await client.get(endpoint, **kwargs)
        elif method.upper() == "POST":
            return await client.post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            return await client.put(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            return await client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(f"Unexpected error calling auth service: {e}", service_name="auth-service")

async def call_product_service(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Call product service with error handling"""
    client = service_client_manager.get_client("product-service")
    if not client:
        raise ServiceError("Product service client not available", service_name="product-service")
    
    try:
        if method.upper() == "GET":
            return await client.get(endpoint, **kwargs)
        elif method.upper() == "POST":
            return await client.post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            return await client.put(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            return await client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(f"Unexpected error calling product service: {e}", service_name="product-service")

async def call_cart_service(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Call cart service with error handling"""
    client = service_client_manager.get_client("cart-service")
    if not client:
        raise ServiceError("Cart service client not available", service_name="cart-service")
    
    try:
        if method.upper() == "GET":
            return await client.get(endpoint, **kwargs)
        elif method.upper() == "POST":
            return await client.post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            return await client.put(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            return await client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(f"Unexpected error calling cart service: {e}", service_name="cart-service")

async def call_order_service(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Call order service with error handling"""
    client = service_client_manager.get_client("order-service")
    if not client:
        raise ServiceError("Order service client not available", service_name="order-service")
    
    try:
        if method.upper() == "GET":
            return await client.get(endpoint, **kwargs)
        elif method.upper() == "POST":
            return await client.post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            return await client.put(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            return await client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(f"Unexpected error calling order service: {e}", service_name="order-service")

async def call_delivery_service(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Call delivery service with error handling"""
    client = service_client_manager.get_client("delivery-service")
    if not client:
        raise ServiceError("Delivery service client not available", service_name="delivery-service")
    
    try:
        if method.upper() == "GET":
            return await client.get(endpoint, **kwargs)
        elif method.upper() == "POST":
            return await client.post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            return await client.put(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            return await client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(f"Unexpected error calling delivery service: {e}", service_name="delivery-service")

async def call_notification_service(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Call notification service with error handling"""
    client = service_client_manager.get_client("notification-service")
    if not client:
        raise ServiceError("Notification service client not available", service_name="notification-service")
    
    try:
        if method.upper() == "GET":
            return await client.get(endpoint, **kwargs)
        elif method.upper() == "POST":
            return await client.post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            return await client.put(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            return await client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(f"Unexpected error calling notification service: {e}", service_name="notification-service")

# Graceful degradation utilities
class ServiceFallback:
    """Provides fallback responses when services are unavailable"""
    
    @staticmethod
    def get_user_fallback() -> Dict[str, Any]:
        """Fallback user data when auth service is unavailable"""
        return {
            "id": "unknown",
            "email": "unknown@example.com",
            "name": "Unknown User",
            "is_authenticated": False,
            "fallback": True
        }
    
    @staticmethod
    def get_product_fallback(product_id: str = None) -> Dict[str, Any]:
        """Fallback product data when product service is unavailable"""
        return {
            "id": product_id or "unknown",
            "name": "Product Unavailable",
            "description": "Product information is temporarily unavailable",
            "price": 0.0,
            "available": False,
            "fallback": True
        }
    
    @staticmethod
    def get_cart_fallback(user_id: str = None) -> Dict[str, Any]:
        """Fallback cart data when cart service is unavailable"""
        return {
            "user_id": user_id or "unknown",
            "items": [],
            "total": 0.0,
            "item_count": 0,
            "fallback": True
        }
    
    @staticmethod
    def get_order_fallback(order_id: str = None) -> Dict[str, Any]:
        """Fallback order data when order service is unavailable"""
        return {
            "id": order_id or "unknown",
            "status": "unknown",
            "total": 0.0,
            "items": [],
            "fallback": True
        }

# Context manager for graceful service calls
class GracefulServiceCall:
    """Context manager for service calls with fallback support"""
    
    def __init__(self, service_name: str, fallback_func=None):
        self.service_name = service_name
        self.fallback_func = fallback_func
        self.error = None
        self.result = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, ServiceError):
            self.error = exc_val
            logger.warning(f"Service call to {self.service_name} failed: {exc_val}")
            
            if self.fallback_func:
                try:
                    self.result = self.fallback_func()
                    logger.info(f"Using fallback response for {self.service_name}")
                except Exception as fallback_error:
                    logger.error(f"Fallback function failed for {self.service_name}: {fallback_error}")
            
            return True  # Suppress the exception
        
        return False
    
    def has_error(self) -> bool:
        """Check if the service call resulted in an error"""
        return self.error is not None
    
    def get_result(self) -> Any:
        """Get the result (either from service or fallback)"""
        return self.result