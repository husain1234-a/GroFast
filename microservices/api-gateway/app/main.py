from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from .routes import auth, products, cart, orders, delivery, notifications, admin
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.auth import AuthMiddleware
from .config import settings
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from middleware.security import SecurityHeadersMiddleware, RateLimitMiddleware as SharedRateLimit

app = FastAPI(
    title="Blinkit Clone - API Gateway",
    description="Microservices API Gateway",
    version="1.0.0"
)

# Middleware (order matters - Security first, then CORS, then Auth, then Rate Limiting)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SharedRateLimit, requests_per_minute=100)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# Add monitoring and enhanced logging
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from metrics import metrics, MetricsMiddleware
from logging import setup_logging, RequestLoggingMiddleware, HealthCheckLogger
from health_checks import HealthChecker, create_fastapi_health_endpoints

# Setup enhanced logging
logger = setup_logging("api-gateway", log_level="INFO", enable_json=True)
health_logger = HealthCheckLogger(logger, "api-gateway")

# Setup health checker
health_checker = HealthChecker("API Gateway", logger)

# Add enhanced middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware, logger=logger)

# Register dependency health checks
async def check_auth_service():
    return await health_checker.check_http_service("auth-service", f"{SERVICES['auth']}/health")

async def check_product_service():
    return await health_checker.check_http_service("product-service", f"{SERVICES['product']}/health")

async def check_cart_service():
    return await health_checker.check_http_service("cart-service", f"{SERVICES['cart']}/health")

async def check_order_service():
    return await health_checker.check_http_service("order-service", f"{SERVICES['order']}/health")

async def check_delivery_service():
    return await health_checker.check_http_service("delivery-service", f"{SERVICES['delivery']}/health")

async def check_notification_service():
    return await health_checker.check_http_service("notification-service", f"{SERVICES['notification']}/health")

# Register all dependency checks
health_checker.register_dependency_check("auth-service", check_auth_service)
health_checker.register_dependency_check("product-service", check_product_service)
health_checker.register_dependency_check("cart-service", check_cart_service)
health_checker.register_dependency_check("order-service", check_order_service)
health_checker.register_dependency_check("delivery-service", check_delivery_service)
health_checker.register_dependency_check("notification-service", check_notification_service)

# Create enhanced health check endpoints
create_fastapi_health_endpoints(app, health_checker)

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    return metrics.get_metrics()

# Prometheus metrics endpoint
@app.get("/metrics/prometheus")
async def get_prometheus_metrics():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=metrics.get_prometheus_format(),
        media_type="text/plain"
    )

# Service discovery
SERVICES = {
    "auth": "http://localhost:8001",
    "product": "http://localhost:8002", 
    "cart": "http://localhost:8003",
    "order": "http://localhost:8004",
    "delivery": "http://localhost:8005",
    "notification": "http://localhost:8006"
}

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(cart.router, prefix="/cart", tags=["Cart"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(delivery.router, prefix="/delivery", tags=["Delivery"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )