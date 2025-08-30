from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from .services.delivery_service import DeliveryService
from .database import get_db
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from logging import setup_logging, RequestLoggingMiddleware, HealthCheckLogger
from health_checks import HealthChecker, create_fastapi_health_endpoints
from metrics import metrics, MetricsMiddleware

app = FastAPI(title="Delivery Service", version="1.0.0")

# Setup enhanced logging
logger = setup_logging("delivery-service", log_level="INFO", enable_json=True)
health_logger = HealthCheckLogger(logger, "delivery-service")

# Setup health checker
health_checker = HealthChecker("Delivery Service", logger)

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
        # For delivery service, extract delivery partner UID from token
        firebase_uid = firebase_token.replace('Bearer ', '') if firebase_token.startswith('Bearer ') else firebase_token
        return {
            "firebase_uid": firebase_uid,
            "source": "token"
        }
    
    # No user context available
    raise HTTPException(status_code=401, detail="User authentication required")

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

# Register Supabase health check
async def check_supabase():
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        return await health_checker.check_http_service("supabase", f"{supabase_url}/rest/v1/")
    else:
        from health_checks import HealthCheckResult
        return HealthCheckResult(
            name="supabase",
            status="healthy",
            response_time_ms=0,
            details={"note": "Supabase not configured"}
        )

health_checker.register_dependency_check("database", check_database)
health_checker.register_dependency_check("supabase", check_supabase)

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

@app.get("/delivery/me")
async def get_delivery_partner(
    request: Request, 
    firebase_token: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    context = await get_user_context(request, firebase_token)
    firebase_uid = context.get("firebase_uid", f"user_{context.get('user_id', 1)}")
    
    partner = await DeliveryService.get_delivery_partner(db, firebase_uid)
    if not partner:
        return {"id": None, "name": "Unknown Partner", "status": "not_registered"}
    
    return {
        "id": partner.id,
        "name": partner.name,
        "status": partner.status.value,
        "phone": partner.phone,
        "current_latitude": partner.current_latitude,
        "current_longitude": partner.current_longitude
    }

@app.put("/delivery/status")
async def update_status(
    status: str,
    request: Request,
    firebase_token: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    context = await get_user_context(request, firebase_token)
    firebase_uid = context.get("firebase_uid", f"user_{context.get('user_id', 1)}")
    
    from .models.delivery import DeliveryStatus
    try:
        delivery_status = DeliveryStatus(status)
        partner = await DeliveryService.update_status(db, firebase_uid, delivery_status)
        return {"status": "updated", "partner_id": partner.id if partner else None}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

@app.post("/delivery/location")
async def update_location(
    latitude: float,
    longitude: float,
    order_id: int = None,
    request: Request = None,
    firebase_token: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    context = await get_user_context(request, firebase_token)
    firebase_uid = context.get("firebase_uid", f"user_{context.get('user_id', 1)}")
    
    service = DeliveryService()
    partner = await service.update_location(db, firebase_uid, latitude, longitude, order_id)
    return {
        "message": "Location updated",
        "partner_id": partner.id if partner else None,
        "latitude": latitude,
        "longitude": longitude
    }

@app.get("/delivery/orders")
async def get_orders(
    request: Request,
    firebase_token: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    context = await get_user_context(request, firebase_token)
    firebase_uid = context.get("firebase_uid", f"user_{context.get('user_id', 1)}")
    
    orders = await DeliveryService.get_assigned_orders(db, firebase_uid)
    return orders