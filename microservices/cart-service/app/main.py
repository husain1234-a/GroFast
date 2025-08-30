from fastapi import FastAPI, Depends, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas.cart import CartItemCreate, CartItemRemove
from .services.cart_service import CartService
from .database import get_db
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from logging import setup_logging, RequestLoggingMiddleware, HealthCheckLogger
from health_checks import HealthChecker, create_fastapi_health_endpoints
from metrics import metrics, MetricsMiddleware

app = FastAPI(title="Cart Service", version="1.0.0")

# Setup enhanced logging
logger = setup_logging("cart-service", log_level="INFO", enable_json=True)
health_logger = HealthCheckLogger(logger, "cart-service")

# Setup health checker
health_checker = HealthChecker("Cart Service", logger)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

# Add enhanced middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware, logger=logger)

async def get_user_context(request: Request, firebase_token: str = Query(None)):
    """Extract user context from headers (preferred) or query parameter (fallback)"""
    
    # Try to get user ID from API Gateway headers first
    user_id_header = request.headers.get("X-User-ID")
    user_email_header = request.headers.get("X-User-Email")
    
    if user_id_header:
        try:
            user_id = int(user_id_header)
            return {
                "user_id": user_id,
                "email": user_email_header,
                "source": "header"
            }
        except ValueError:
            pass
    
    # Fallback to token-based extraction for backward compatibility
    if firebase_token:
        user_id = int(firebase_token.split('_')[-1]) if '_' in firebase_token else 1
        return {
            "user_id": user_id,
            "email": f"user{user_id}@example.com",
            "source": "token"
        }
    
    # No user context available
    raise HTTPException(status_code=401, detail="User authentication required")

async def get_user_id(request: Request, firebase_token: str = Query(None)):
    """Get user ID from context - backward compatibility function"""
    context = await get_user_context(request, firebase_token)
    return context["user_id"]

# Register database health check
async def check_database():
    try:
        async with get_db() as db:
            return await health_checker.check_database(lambda: db, "SELECT 1")
    except Exception as e:
        logger.error(f"Database health check setup failed: {e}")
        from health_checks import HealthCheckResult
        return HealthCheckResult(
            name="database",
            status="unhealthy",
            response_time_ms=0,
            error=str(e)
        )

# Register Redis health check
async def check_redis():
    # Assuming Redis URL is available in environment
    import os
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return await health_checker.check_redis(redis_url)

# Register external service checks
async def check_auth_service():
    auth_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    return await health_checker.check_http_service("auth-service", f"{auth_url}/health")

async def check_product_service():
    product_url = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002")
    return await health_checker.check_http_service("product-service", f"{product_url}/health")

health_checker.register_dependency_check("database", check_database)
health_checker.register_dependency_check("redis", check_redis)
health_checker.register_dependency_check("auth-service", check_auth_service)
health_checker.register_dependency_check("product-service", check_product_service)

# Create enhanced health check endpoints
create_fastapi_health_endpoints(app, health_checker)

# Metrics endpoints
@app.get("/metrics")
async def get_metrics():
    return metrics.get_metrics()

@app.get("/metrics/prometheus")
async def get_prometheus_metrics():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=metrics.get_prometheus_format(),
        media_type="text/plain"
    )

@app.get("/cart")
async def get_cart(user_id: int = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    return await CartService.get_cart_with_details(db, user_id)

@app.post("/cart/add")
async def add_to_cart(item: CartItemCreate, user_id: int = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    return await CartService.add_item(db, user_id, item)

@app.post("/cart/remove")
async def remove_from_cart(item: CartItemRemove, user_id: int = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    return await CartService.remove_item(db, user_id, item.product_id)

@app.delete("/cart/clear")
async def clear_cart(user_id: int = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    return await CartService.clear_cart(db, user_id)