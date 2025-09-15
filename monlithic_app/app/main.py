from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
import time
import redis
import uuid
# Handle both direct execution and module import
try:
    from .config.settings import settings
    from .routes import auth, products, cart, orders, delivery, notifications, admin
    from .utils.logger import logger
except ImportError:
    # Direct execution - add parent directory to path
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config.settings import settings
    from app.routes import auth, products, cart, orders, delivery, notifications, admin
    from app.utils.logger import logger


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

# Redis disabled for development
redis_client = None

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=(
        ["*"] if settings.debug 
        else ["yourdomain.com", "*.yourdomain.com"]
    )
)

# Middleware disabled for development
# @app.middleware("http")
# async def add_request_id(request: Request, call_next):
#     response = await call_next(request)
#     return response

# Rate limiting disabled for development
# @app.middleware("http")
# async def rate_limit_middleware(request: Request, call_next):
#     response = await call_next(request)
#     return response

# Logging middleware disabled for development
# @app.middleware("http")
# async def logging_middleware(request: Request, call_next):
#     response = await call_next(request)
#     return response

# Simple Health Check
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Blinkit Clone API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Contact admin for API documentation"
    }

# Fast test endpoint
@app.get("/test")
async def test():
    return {"status": "ok", "timestamp": time.time()}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

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