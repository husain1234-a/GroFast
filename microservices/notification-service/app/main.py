from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .services.notification_service import NotificationService
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from logging import setup_logging, RequestLoggingMiddleware, HealthCheckLogger
from health_checks import HealthChecker, create_fastapi_health_endpoints
from metrics import metrics, MetricsMiddleware

app = FastAPI(title="Notification Service", version="1.0.0")

# Setup enhanced logging
logger = setup_logging("notification-service", log_level="INFO", enable_json=True)
health_logger = HealthCheckLogger(logger, "notification-service")

# Setup health checker
health_checker = HealthChecker("Notification Service", logger)

notification_service = NotificationService()

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

class FCMRequest(BaseModel):
    fcm_tokens: List[str]
    title: str
    body: str
    data: Optional[dict] = None

class OrderNotificationRequest(BaseModel):
    user_id: int
    order_id: int
    status: str

class DeliveryNotificationRequest(BaseModel):
    user_id: int
    partner_name: str
    eta_minutes: int

class InvoiceEmailRequest(BaseModel):
    user_email: str
    order_data: Dict[str, Any]

# Register Redis health check
async def check_redis():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return await health_checker.check_redis(redis_url)

# Register FCM service health check
async def check_fcm_service():
    fcm_server_key = os.getenv("FCM_SERVER_KEY")
    if fcm_server_key and not fcm_server_key.startswith("AAAA1234567890"):  # Not dummy key
        # FCM doesn't have a direct health endpoint, so we'll just check if key is configured
        from health_checks import HealthCheckResult
        return HealthCheckResult(
            name="fcm",
            status="healthy",
            response_time_ms=0,
            details={"configured": True}
        )
    else:
        from health_checks import HealthCheckResult
        return HealthCheckResult(
            name="fcm",
            status="degraded",
            response_time_ms=0,
            details={"configured": False, "note": "Using dummy FCM key"}
        )

health_checker.register_dependency_check("redis", check_redis)
health_checker.register_dependency_check("fcm", check_fcm_service)

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

@app.post("/notifications/fcm")
async def send_fcm_notification(request: FCMRequest):
    return await notification_service.send_fcm_notification(
        request.fcm_tokens, request.title, request.body, request.data
    )

@app.post("/notifications/order")
async def send_order_notification(request: OrderNotificationRequest):
    return await notification_service.send_order_notification(
        request.user_id, request.order_id, request.status
    )

@app.post("/notifications/delivery")
async def send_delivery_notification(request: DeliveryNotificationRequest):
    return await notification_service.send_delivery_notification(
        request.user_id, request.partner_name, request.eta_minutes
    )

@app.post("/notifications/invoice-email")
async def send_invoice_email(request: InvoiceEmailRequest):
    return await notification_service.send_invoice_email(
        request.user_email, request.order_data
    )