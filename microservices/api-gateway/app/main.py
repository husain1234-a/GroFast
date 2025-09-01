from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
import logging

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

app = FastAPI(
    title="Blinkit Clone - API Gateway",
    description="Microservices API Gateway",
    version="1.0.0"
)

# Import config with fallback
try:
    from .config import settings
    cors_origins = settings.cors_origins
except Exception as e:
    print(f"Config import failed: {e}")
    cors_origins = ["*"]

# Security middleware with fallback
try:
    from middleware.security import SecurityHeadersMiddleware, RateLimitMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    print("✓ Security middleware loaded")
except ImportError:
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            return response
    
    app.add_middleware(SecurityHeadersMiddleware)
    print("✓ Fallback security middleware loaded")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Auth middleware with fallback
try:
    from .middleware.auth import AuthMiddleware
    app.add_middleware(AuthMiddleware)
    print("✓ Auth middleware loaded")
except Exception as e:
    print(f"✗ Auth middleware failed: {e}")

# Health checks
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "API Gateway"}

@app.get("/metrics")
async def get_metrics():
    return {"status": "metrics endpoint", "service": "API Gateway"}

# Import routes with individual error handling
routes_loaded = []
routes_failed = []

try:
    from .routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    routes_loaded.append("auth")
except Exception as e:
    routes_failed.append(f"auth: {e}")

try:
    from .routes.products import router as products_router
    app.include_router(products_router, prefix="/products", tags=["Products"])
    routes_loaded.append("products")
except Exception as e:
    routes_failed.append(f"products: {e}")

try:
    from .routes.cart import router as cart_router
    app.include_router(cart_router, prefix="/cart", tags=["Cart"])
    routes_loaded.append("cart")
except Exception as e:
    routes_failed.append(f"cart: {e}")

try:
    from .routes.orders import router as orders_router
    app.include_router(orders_router, prefix="/orders", tags=["Orders"])
    routes_loaded.append("orders")
except Exception as e:
    routes_failed.append(f"orders: {e}")

try:
    from .routes.delivery import router as delivery_router
    app.include_router(delivery_router, prefix="/delivery", tags=["Delivery"])
    routes_loaded.append("delivery")
except Exception as e:
    routes_failed.append(f"delivery: {e}")

try:
    from .routes.notifications import router as notifications_router
    app.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
    routes_loaded.append("notifications")
except Exception as e:
    routes_failed.append(f"notifications: {e}")

try:
    from .routes.admin import router as admin_router
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])
    routes_loaded.append("admin")
except Exception as e:
    routes_failed.append(f"admin: {e}")

print(f"✓ Routes loaded: {routes_loaded}")
if routes_failed:
    print(f"✗ Routes failed: {routes_failed}")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger = logging.getLogger(__name__)
    error_id = str(hash(str(exc)))[:8]
    
    logger.error(
        f"Unhandled exception [{error_id}]: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
            "error_id": error_id,
            "client_host": getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": error_id,
            "timestamp": str(exc.__class__.__name__)
        }
    )