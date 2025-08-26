from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import redis
from .config.settings import settings
from .routes import auth, products, cart, orders, delivery, notifications, admin
from .utils.logger import logger

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Ultra-fast grocery delivery platform",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

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
    allowed_hosts=["*"] if settings.debug else ["yourdomain.com", "*.yourdomain.com"]
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    try:
        current_requests = redis_client.get(key)
        if current_requests is None:
            redis_client.setex(key, 60, 1)  # 1 request in 60 seconds window
        else:
            current_requests = int(current_requests)
            if current_requests >= 100:  # 100 requests per minute
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"}
                )
            redis_client.incr(key)
    except Exception as e:
        logger.error(f"Rate limiting error: {e}")
    
    response = await call_next(request)
    return response

# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    
    return response

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}

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

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(delivery.router)
app.include_router(notifications.router)
app.include_router(admin.router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )