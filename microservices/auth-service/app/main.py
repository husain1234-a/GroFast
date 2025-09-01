from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, internal
from .config import settings
from .database import db_manager
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from custom_logging import setup_logging
from health_checks import HealthChecker, create_fastapi_health_endpoints
from startup_validation import create_startup_event_handler

app = FastAPI(
    title="Auth Service",
    description="Authentication and User Management Service",
    version="1.0.0"
)

# Setup logging
logger = setup_logging("auth-service", log_level="INFO")

# Add startup validation
app.add_event_handler(
    "startup",
    create_startup_event_handler("auth-service", db_manager.get_db, settings)
)

# Setup comprehensive health checks
health_checker = HealthChecker("auth-service", logger)

# Register database health check
async def check_database():
    return await health_checker.check_database(db_manager.get_db)

health_checker.register_check("database", check_database)

# Register Redis health check
async def check_redis():
    return await health_checker.check_redis(settings.redis_url)

health_checker.register_check("redis", check_redis)

# Create health endpoints
create_fastapi_health_endpoints(app, health_checker)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(internal.router, prefix="/internal", tags=["Internal"])