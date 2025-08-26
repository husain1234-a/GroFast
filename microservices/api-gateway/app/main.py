from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from .routes import auth, products, cart, orders, delivery, notifications, admin
from .middleware.rate_limit import RateLimitMiddleware
from .config import settings

app = FastAPI(
    title="Blinkit Clone - API Gateway",
    description="Microservices API Gateway",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "API Gateway"}

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