from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, internal
from .config import settings
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

app = FastAPI(
    title="Auth Service",
    description="Authentication and User Management Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Auth Service"}

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(internal.router, prefix="/internal", tags=["Internal"])