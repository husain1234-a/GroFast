from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, internal
from .config import settings
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from logging import setup_logging, RequestLoggingMiddleware, HealthCheckLogger
from health_checks import HealthChecker, create_fastapi_health_endpoints
from metrics import metrics, MetricsMiddleware

app = FastAPI(
    title="Auth Service",
    description="Authentication and User Management Service",
    version="1.0.0"
)

# Setup enhanced logging
logger = setup_logging("auth-service", log_level="INFO", enable_json=True)
health_logger = HealthCheckLogger(logger, "auth-service")

# Setup health checker
health_checker = HealthChecker("Auth Service", logger)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add enhanced middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware, logger=logger)

# Register database health check
async def check_database():
    try:
        from .database import get_db
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

# Register Redis health check if configured
async def check_redis():
    redis_url = getattr(settings, 'redis_url', None)
    if redis_url:
        return await health_checker.check_redis(redis_url)
    else:
        from health_checks import HealthCheckResult
        return HealthCheckResult(
            name="redis",
            status="healthy",
            response_time_ms=0,
            details={"note": "Redis not configured"}
        )

health_checker.register_dependency_check("database", check_database)
health_checker.register_dependency_check("redis", check_redis)

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

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(internal.router, prefix="/internal", tags=["Internal"])