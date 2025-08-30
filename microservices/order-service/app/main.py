from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from .services.order_service import OrderService
from .database import get_db
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from logging import setup_logging, RequestLoggingMiddleware, HealthCheckLogger
from health_checks import HealthChecker, create_fastapi_health_endpoints
from metrics import metrics, MetricsMiddleware

app = FastAPI(title="Order Service", version="1.0.0")

# Setup enhanced logging
logger = setup_logging("order-service", log_level="INFO", enable_json=True)
health_logger = HealthCheckLogger(logger, "order-service")

# Setup health checker
health_checker = HealthChecker("Order Service", logger)

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

# Register external service checks
async def check_auth_service():
    auth_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    return await health_checker.check_http_service("auth-service", f"{auth_url}/health")

async def check_cart_service():
    cart_url = os.getenv("CART_SERVICE_URL", "http://localhost:8003")
    return await health_checker.check_http_service("cart-service", f"{cart_url}/health")

async def check_notification_service():
    notification_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8006")
    return await health_checker.check_http_service("notification-service", f"{notification_url}/health")

health_checker.register_dependency_check("database", check_database)
health_checker.register_dependency_check("auth-service", check_auth_service)
health_checker.register_dependency_check("cart-service", check_cart_service)
health_checker.register_dependency_check("notification-service", check_notification_service)

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

@app.post("/orders/create", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    user_id: int = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    order = await OrderService.create_order(db, user_id, order_data)
    return OrderResponse.model_validate(order)

@app.get("/orders/my-orders", response_model=List[OrderResponse])
async def get_my_orders(
    user_id: int = Depends(get_user_id),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    orders = await OrderService.get_user_orders(db, user_id, limit, offset)
    return [OrderResponse.model_validate(order) for order in orders]

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    user_id: int = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    order = await OrderService.get_order_by_id(db, order_id, user_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse.model_validate(order)

@app.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    order = await OrderService.update_order_status(db, order_id, status_update.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse.model_validate(order)