from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import httpx
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from custom_logging import setup_logging

app = FastAPI(
    title="Admin Service",
    description="Administrative Management Service",
    version="1.0.0"
)

logger = setup_logging("admin-service", log_level="INFO")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_admin(x_admin_key: str = Header(...)):
    """Verify admin API key"""
    if x_admin_key != "admin_secret_key":
        raise HTTPException(status_code=403, detail="Admin access required")

@app.get("/admin/stats")
async def get_dashboard_stats(_: None = Depends(verify_admin)):
    """Get dashboard statistics"""
    try:
        async with httpx.AsyncClient() as client:
            # Get user count from auth service
            users_response = await client.get("http://auth-service:8000/internal/users/count")
            user_count = users_response.json().get("count", 0) if users_response.status_code == 200 else 0
            
            # Get product count from product service
            products_response = await client.get("http://product-service:8000/products/count")
            product_count = products_response.json().get("count", 0) if products_response.status_code == 200 else 0
            
            # Get order count from order service
            orders_response = await client.get("http://order-service:8000/orders/count")
            order_count = orders_response.json().get("count", 0) if orders_response.status_code == 200 else 0
            
            # Get delivery stats from delivery service
            delivery_response = await client.get("http://delivery-service:8000/delivery/internal/stats")
            delivery_stats = delivery_response.json() if delivery_response.status_code == 200 else {}
            active_deliveries = delivery_stats.get("active_partners", 0)
            
            return {
                "total_users": user_count,
                "total_products": product_count,
                "total_orders": order_count,
                "active_deliveries": active_deliveries
            }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            "total_users": 0,
            "total_products": 0,
            "total_orders": 0,
            "active_deliveries": 0
        }

@app.get("/admin/users")
async def get_users(
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(verify_admin)
):
    """Get users list"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://auth-service:8000/internal/users?limit={limit}&offset={offset}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"users": [], "total": 0}
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return {"users": [], "total": 0}

@app.get("/admin/products")
async def get_products(
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(verify_admin)
):
    """Get products list"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://product-service:8000/admin/products?limit={limit}&offset={offset}",
                headers={"X-Admin-Key": "admin_secret_key"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return []
    except Exception as e:
        logger.error(f"Failed to get products: {e}")
        return []

@app.post("/admin/products/{product_id}/restock")
async def restock_product(
    product_id: int,
    quantity_to_add: int,
    _: None = Depends(verify_admin)
):
    """Restock product inventory"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://product-service:8000/admin/products/{product_id}/restock",
                params={"quantity_to_add": quantity_to_add},
                headers={"X-Admin-Key": "admin_secret_key"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Restock failed")
    except Exception as e:
        logger.error(f"Failed to restock product: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/orders")
async def get_orders(
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(verify_admin)
):
    """Get orders list"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://order-service:8000/admin/orders?limit={limit}&offset={offset}",
                headers={"X-Admin-Key": "admin_secret_key"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return []
    except Exception as e:
        logger.error(f"Failed to get orders: {e}")
        return []

@app.put("/admin/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str,
    _: None = Depends(verify_admin)
):
    """Update order status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://order-service:8000/orders/{order_id}/status",
                json={"status": status}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Status update failed")
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "admin-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)