from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import products
from .config import settings
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

app = FastAPI(
    title="Product Service",
    description="Product Catalog Management Service",
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
    return {"status": "healthy", "service": "Product Service"}

app.include_router(products.router, tags=["Products"])