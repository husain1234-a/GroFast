#!/usr/bin/env python3
"""Standalone API Gateway that works without other services"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Dict, Any

app = FastAPI(title="GroFast - Standalone Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
mock_users = {}
mock_products = [
    {"id": 1, "name": "Milk", "price": 60.0, "category_id": 1, "stock_quantity": 50, "is_active": True},
    {"id": 2, "name": "Bread", "price": 40.0, "category_id": 2, "stock_quantity": 30, "is_active": True},
    {"id": 3, "name": "Eggs", "price": 80.0, "category_id": 1, "stock_quantity": 100, "is_active": True},
]
mock_categories = [
    {"id": 1, "name": "Dairy", "is_active": True},
    {"id": 2, "name": "Bakery", "is_active": True},
]
mock_carts = {}
mock_orders = {}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Standalone API Gateway"}

# Auth endpoints
@app.post("/auth/verify-otp")
async def verify_otp(request: Request):
    body = await request.json()
    user_id = len(mock_users) + 1
    user = {
        "id": user_id,
        "firebase_uid": f"user_{body.get('firebase_id_token', 'demo')[-8:]}",
        "email": "demo@example.com",
        "name": "Demo User",
        "phone": None,
        "address": None,
        "fcm_token": None,
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z"
    }
    mock_users[user_id] = user
    return user

@app.get("/auth/me")
async def get_me(firebase_token: str = "demo"):
    return {
        "id": 1,
        "firebase_uid": "demo_user",
        "email": "demo@example.com",
        "name": "Demo User",
        "phone": None,
        "address": None,
        "fcm_token": None,
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z"
    }

# Product endpoints
@app.get("/products/categories")
async def get_categories():
    return mock_categories

@app.get("/products")
async def get_products(category_id: int = None, search: str = None, limit: int = 50, offset: int = 0):
    products = mock_products
    if category_id:
        products = [p for p in products if p["category_id"] == category_id]
    if search:
        products = [p for p in products if search.lower() in p["name"].lower()]
    return products[offset:offset+limit]

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    product = next((p for p in mock_products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Cart endpoints
@app.get("/cart")
async def get_cart(firebase_token: str = "demo"):
    # Extract user ID from token (simplified for demo)
    if not firebase_token or firebase_token == "demo":
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    # In production, validate JWT token and extract user_id
    user_id = hash(firebase_token) % 1000 + 1  # Simple hash for demo
    cart = mock_carts.get(user_id, {"id": 1, "user_id": user_id, "items": [], "total_amount": 0, "total_items": 0})
    return cart

@app.post("/cart/add")
async def add_to_cart(request: Request, firebase_token: str = "demo"):
    body = await request.json()
    
    # Validate token
    if not firebase_token or firebase_token == "demo":
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    # Extract user ID from token
    user_id = hash(firebase_token) % 1000 + 1
    product_id = body["product_id"]
    quantity = body.get("quantity", 1)
    
    product = next((p for p in mock_products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if user_id not in mock_carts:
        mock_carts[user_id] = {"id": 1, "user_id": user_id, "items": [], "total_amount": 0, "total_items": 0}
    
    cart = mock_carts[user_id]
    existing_item = next((item for item in cart["items"] if item["product_id"] == product_id), None)
    
    if existing_item:
        existing_item["quantity"] += quantity
    else:
        cart["items"].append({
            "id": len(cart["items"]) + 1,
            "product_id": product_id,
            "quantity": quantity,
            "product_name": product["name"],
            "product_price": product["price"]
        })
    
    # Recalculate totals
    cart["total_amount"] = sum(item["product_price"] * item["quantity"] for item in cart["items"])
    cart["total_items"] = sum(item["quantity"] for item in cart["items"])
    
    return cart

@app.delete("/cart/clear")
async def clear_cart(firebase_token: str = "demo"):
    user_id = 1
    mock_carts[user_id] = {"id": 1, "user_id": user_id, "items": [], "total_amount": 0, "total_items": 0}
    return mock_carts[user_id]

# Order endpoints
@app.post("/orders/create")
async def create_order(request: Request, firebase_token: str = "demo"):
    body = await request.json()
    user_id = 1
    cart = mock_carts.get(user_id, {"items": [], "total_amount": 0})
    
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    order_id = len(mock_orders) + 1
    order = {
        "id": order_id,
        "user_id": user_id,
        "total_amount": cart["total_amount"],
        "delivery_fee": 20.0 if cart["total_amount"] < 199 else 0.0,
        "status": "pending",
        "delivery_address": body["delivery_address"],
        "items": cart["items"].copy(),
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    mock_orders[order_id] = order
    mock_carts[user_id] = {"id": 1, "user_id": user_id, "items": [], "total_amount": 0, "total_items": 0}
    
    return order

@app.get("/orders/my-orders")
async def get_my_orders(firebase_token: str = "demo"):
    # Validate token
    if not firebase_token or firebase_token == "demo":
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    # Extract user ID from token
    user_id = hash(firebase_token) % 1000 + 1
    user_orders = [order for order in mock_orders.values() if order["user_id"] == user_id]
    return user_orders

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)