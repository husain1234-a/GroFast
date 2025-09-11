from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
import time
import redis
import uuid
from .config.settings import settings
from .routes import auth, products, cart, orders, delivery, notifications, admin
from .utils.logger import logger


class CustomHTTPException(HTTPException):
    """Custom HTTP exception with error codes"""
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        error_code: str = None
    ):
        super().__init__(status_code, detail)
        self.error_code = error_code

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Ultra-fast grocery delivery platform",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Security scheme
security = HTTPBearer()

# Redis client for rate limiting
redis_client = redis.from_url(settings.redis_url)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=(
        ["*"] if settings.debug 
        else ["yourdomain.com", "*.yourdomain.com"]
    )
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracing"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Enhanced rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Enhanced rate limiting with different limits per endpoint type"""
    client_ip = request.client.host
    path = request.url.path
    method = request.method
    
    # Different limits for different endpoint types
    if path.startswith("/auth/"):
        limit, window = 10, 60  # 10 auth requests per minute
    elif path.startswith("/orders/"):
        limit, window = 30, 60  # 30 order requests per minute
    elif method == "POST":
        limit, window = 50, 60  # 50 POST requests per minute
    else:
        limit, window = 100, 60  # 100 general requests per minute
    
    key = f"rate_limit:{client_ip}:{path.split('/')[1] if '/' in path else 'root'}"
    
    try:
        current_requests = redis_client.get(key)
        if current_requests is None:
            redis_client.setex(key, window, 1)
        else:
            current_requests = int(current_requests)
            if current_requests >= limit:
                request_id = getattr(request.state, 'request_id', 'unknown')
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "request_id": request_id,
                        "retry_after": window
                    }
                )
            redis_client.incr(key)
    except Exception as e:
        logger.error(f"Rate limiting error: {e}")
    
    response = await call_next(request)
    return response

# Enhanced request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Enhanced logging with request ID and more details"""
    start_time = time.time()
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Log request start with structured data
    logger.bind(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else 'unknown',
        query_string=str(request.url.query) if request.url.query else None
    ).info(f"Request started: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Log request completion with structured data
    logger.bind(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=process_time * 1000,
        client_ip=request.client.host if request.client else 'unknown'
    ).info(f"Request completed: {request.method} {request.url.path} - {response.status_code}")
    
    return response

# Enhanced Health Checks
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'microservices', 'shared'))

from health_checks import HealthChecker, create_fastapi_health_endpoints
from metrics import metrics, MetricsMiddleware
from logging import setup_logging, RequestLoggingMiddleware

# Setup enhanced logging
enhanced_logger = setup_logging("main-application", log_level="INFO", enable_json=True)

# Setup health checker
health_checker = HealthChecker("Main Application", enhanced_logger)

# Register database health check
async def check_database():
    from sqlalchemy import text
    from .config.database import AsyncSessionLocal
    
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return await health_checker.check_database(AsyncSessionLocal)
    except Exception as e:
        from health_checks import HealthCheckResult
        return HealthCheckResult(
            name="database",
            status="unhealthy",
            response_time_ms=0,
            error=str(e)
        )

# Register Redis health check
async def check_redis():
    return await health_checker.check_redis(settings.redis_url)

health_checker.register_dependency_check("database", check_database)
health_checker.register_dependency_check("redis", check_redis)

# Create enhanced health check endpoints
create_fastapi_health_endpoints(app, health_checker)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

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

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Blinkit Clone API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Contact admin for API documentation"
    }

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers with API versioning
api_v1 = FastAPI()
api_v1.include_router(auth.router)
api_v1.include_router(products.router)
api_v1.include_router(cart.router)
api_v1.include_router(orders.router)
api_v1.include_router(delivery.router)
api_v1.include_router(notifications.router)
api_v1.include_router(admin.router)

# Mount v1 API
app.mount("/api/v1", api_v1)

# Also include routers at root level for backward compatibility
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(delivery.router)
app.include_router(notifications.router)
app.include_router(admin.router)

# Enhanced exception handlers
@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
    """Handle custom HTTP exceptions with error codes"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.bind(
        request_id=request_id,
        error_code=exc.error_code,
        status_code=exc.status_code,
        path=request.url.path if hasattr(request, 'url') else 'unknown'
    ).error(f"Custom HTTP Exception: {exc.error_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
            "request_id": request_id
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle standard HTTP exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.bind(
        request_id=request_id,
        status_code=exc.status_code,
        path=request.url.path if hasattr(request, 'url') else 'unknown'
    ).warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.bind(
        request_id=request_id,
        exception_type=type(exc).__name__,
        path=request.url.path if hasattr(request, 'url') else 'unknown'
    ).error(f"Unexpected Exception: {type(exc).__name__} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )