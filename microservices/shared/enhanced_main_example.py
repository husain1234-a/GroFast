"""
Enhanced main.py example showing how to integrate the new error handling patterns
This serves as a template for updating service main files
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
import logging

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from service_startup import create_service_startup_manager, create_fastapi_lifespan
from service_clients import service_client_manager, ServiceError
from custom_logging import setup_logging, RequestLoggingMiddleware
from health_checks import HealthChecker, create_fastapi_health_endpoints

# Example for auth-service integration
def create_enhanced_auth_service():
    """Example of how to create an enhanced auth service with new error handling"""
    
    # Import service-specific modules (these would be actual imports in real service)
    # from .routes import auth, internal
    # from .config import settings
    # from .database import db_manager
    
    # For this example, we'll use mock objects
    class MockSettings:
        cors_origins = ["http://localhost:3000"]
        service_name = "auth-service"
        log_level = "INFO"
        
        def get_service_urls(self):
            return {}  # Auth service typically doesn't call other services
    
    class MockDBManager:
        async def get_db(self):
            pass  # Mock database session
    
    settings = MockSettings()
    db_manager = MockDBManager()
    
    # Create startup manager with enhanced error handling
    startup_manager = create_service_startup_manager(
        service_name="auth-service",
        settings=settings,
        db_session_factory=db_manager.get_db
    )
    
    # Add custom initialization steps
    async def initialize_auth_specific():
        """Initialize auth-specific components"""
        logger = logging.getLogger("auth-service")
        logger.info("Initializing Firebase authentication")
        # Initialize Firebase, JWT handlers, etc.
    
    startup_manager.add_initialization_step(initialize_auth_specific, "auth_components")
    
    # Add custom health checks
    async def check_firebase_connectivity():
        """Check Firebase connectivity"""
        # Mock Firebase check
        return {"firebase": "connected"}
    
    startup_manager.add_health_check(check_firebase_connectivity, "firebase")
    
    # Create FastAPI lifespan
    lifespan = create_fastapi_lifespan(startup_manager, settings, db_manager.get_db)
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Enhanced Auth Service",
        description="Authentication and User Management Service with Enhanced Error Handling",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Setup logging
    logger = setup_logging("auth-service", log_level=settings.log_level)
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware, logger=logger)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create health endpoints using startup manager
    @app.get("/health")
    async def health_check():
        """Enhanced health check endpoint"""
        try:
            health_status = await startup_manager.get_health_status()
            
            if health_status["status"] == "healthy":
                return health_status
            else:
                raise HTTPException(status_code=503, detail=health_status)
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=503, 
                detail={
                    "service": "auth-service",
                    "status": "unhealthy",
                    "error": str(e)
                }
            )
    
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with all components"""
        return await startup_manager.get_health_status()
    
    # Example endpoint with enhanced error handling
    @app.post("/auth/login")
    async def login_with_error_handling(credentials: dict):
        """Example login endpoint with enhanced error handling"""
        try:
            # Mock login logic
            logger.info(f"Login attempt for user: {credentials.get('email', 'unknown')}")
            
            # Simulate authentication logic
            if not credentials.get('email') or not credentials.get('password'):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "validation_error",
                        "message": "Email and password are required"
                    }
                )
            
            # Mock successful authentication
            return {
                "access_token": "mock_token",
                "token_type": "bearer",
                "user": {
                    "id": "user123",
                    "email": credentials["email"],
                    "name": "Mock User"
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed for {credentials.get('email', 'unknown')}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "authentication_error",
                    "message": "Authentication service temporarily unavailable"
                }
            )
    
    return app

# Example for API Gateway integration with service calls
def create_enhanced_api_gateway():
    """Example of how to create an enhanced API gateway with service communication"""
    
    class MockSettings:
        cors_origins = ["http://localhost:3000"]
        service_name = "api-gateway"
        log_level = "INFO"
        request_timeout_seconds = 30
        max_retries = 3
        
        def get_service_urls(self):
            return {
                "auth-service": "http://localhost:8001",
                "product-service": "http://localhost:8002",
                "cart-service": "http://localhost:8003",
                "order-service": "http://localhost:8004",
                "delivery-service": "http://localhost:8005",
                "notification-service": "http://localhost:8006"
            }
    
    settings = MockSettings()
    
    # Create startup manager
    startup_manager = create_service_startup_manager(
        service_name="api-gateway",
        settings=settings
    )
    
    # Create FastAPI lifespan
    lifespan = create_fastapi_lifespan(startup_manager, settings)
    
    app = FastAPI(
        title="Enhanced API Gateway",
        description="API Gateway with Enhanced Error Handling and Service Communication",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Setup logging
    logger = setup_logging("api-gateway", log_level=settings.log_level)
    app.add_middleware(RequestLoggingMiddleware, logger=logger)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health endpoints
    @app.get("/health")
    async def health_check():
        """Gateway health check including all downstream services"""
        try:
            health_status = await startup_manager.get_health_status()
            
            if health_status["status"] == "healthy":
                return health_status
            else:
                raise HTTPException(status_code=503, detail=health_status)
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail={"error": str(e)})
    
    # Example endpoint that calls multiple services with error handling
    @app.get("/api/user/{user_id}/dashboard")
    async def get_user_dashboard(user_id: str):
        """Example endpoint that aggregates data from multiple services"""
        from service_clients import (
            call_auth_service, call_product_service, call_cart_service, 
            ServiceFallback, GracefulServiceCall
        )
        
        dashboard_data = {
            "user_id": user_id,
            "user_info": None,
            "recent_products": None,
            "cart_summary": None,
            "errors": []
        }
        
        # Get user info with fallback
        async with GracefulServiceCall("auth-service", ServiceFallback.get_user_fallback) as auth_call:
            try:
                user_response = await call_auth_service(f"/users/{user_id}")
                dashboard_data["user_info"] = user_response
            except ServiceError as e:
                dashboard_data["errors"].append(f"Auth service error: {e}")
        
        if auth_call.has_error():
            dashboard_data["user_info"] = auth_call.get_result()
        
        # Get recent products with fallback
        async with GracefulServiceCall("product-service", lambda: {"products": []}) as product_call:
            try:
                products_response = await call_product_service("/products/recent")
                dashboard_data["recent_products"] = products_response
            except ServiceError as e:
                dashboard_data["errors"].append(f"Product service error: {e}")
        
        if product_call.has_error():
            dashboard_data["recent_products"] = product_call.get_result()
        
        # Get cart summary with fallback
        async with GracefulServiceCall("cart-service", lambda: ServiceFallback.get_cart_fallback(user_id)) as cart_call:
            try:
                cart_response = await call_cart_service(f"/cart/{user_id}")
                dashboard_data["cart_summary"] = cart_response
            except ServiceError as e:
                dashboard_data["errors"].append(f"Cart service error: {e}")
        
        if cart_call.has_error():
            dashboard_data["cart_summary"] = cart_call.get_result()
        
        # Log any service errors for monitoring
        if dashboard_data["errors"]:
            logger.warning(f"Dashboard request for user {user_id} had service errors: {dashboard_data['errors']}")
        
        return dashboard_data
    
    return app

# Usage examples
if __name__ == "__main__":
    # This would be in the actual service main.py files
    
    # For auth-service/app/main.py:
    # app = create_enhanced_auth_service()
    
    # For api-gateway/app/main.py:
    # app = create_enhanced_api_gateway()
    
    pass