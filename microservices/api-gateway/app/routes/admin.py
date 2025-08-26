from fastapi import APIRouter, Request, Query
import httpx
from ..config import settings

router = APIRouter()

@router.get("/stats")
async def get_admin_stats(admin_key: str = Query(...)):
    if admin_key != "admin123":
        return {"error": "Invalid admin key"}
    
    # Aggregate stats from multiple services
    stats = {
        "total_users": 0,
        "total_orders": 0,
        "total_revenue": 0.0,
        "active_delivery_partners": 0
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Get user stats from Auth Service
            auth_response = await client.get(f"{settings.auth_service_url}/internal/stats")
            if auth_response.status_code == 200:
                auth_stats = auth_response.json()
                stats["total_users"] = auth_stats.get("total_users", 0)
            
            # Get order stats from Order Service
            order_response = await client.get(f"{settings.order_service_url}/internal/stats")
            if order_response.status_code == 200:
                order_stats = order_response.json()
                stats["total_orders"] = order_stats.get("total_orders", 0)
                stats["total_revenue"] = order_stats.get("total_revenue", 0.0)
            
            # Get delivery stats from Delivery Service
            delivery_response = await client.get(f"{settings.delivery_service_url}/internal/stats")
            if delivery_response.status_code == 200:
                delivery_stats = delivery_response.json()
                stats["active_delivery_partners"] = delivery_stats.get("active_partners", 0)
    
    except Exception as e:
        stats["error"] = f"Failed to fetch stats: {str(e)}"
    
    return stats

@router.get("/products")
async def get_admin_products(admin_key: str = Query(...)):
    if admin_key != "admin123":
        return {"error": "Invalid admin key"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.product_service_url}/admin/products")
        return response.json()

@router.post("/products")
async def create_admin_product(request: Request, admin_key: str = Query(...)):
    if admin_key != "admin123":
        return {"error": "Invalid admin key"}
    
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.product_service_url}/admin/products",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

@router.get("/orders")
async def get_admin_orders(admin_key: str = Query(...)):
    if admin_key != "admin123":
        return {"error": "Invalid admin key"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.order_service_url}/admin/orders")
        return response.json()