#!/usr/bin/env python3
"""Initialize database with sample data"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import AsyncSessionLocal
from app.models.product import Category, Product
from app.models.delivery import DeliveryPartner, DeliveryStatus

async def init_categories():
    """Create sample categories"""
    categories = [
        {"name": "Fruits & Vegetables", "image_url": "https://via.placeholder.com/200x200?text=Fruits"},
        {"name": "Dairy & Bakery", "image_url": "https://via.placeholder.com/200x200?text=Dairy"},
        {"name": "Snacks & Beverages", "image_url": "https://via.placeholder.com/200x200?text=Snacks"},
        {"name": "Personal Care", "image_url": "https://via.placeholder.com/200x200?text=Care"},
        {"name": "Household Items", "image_url": "https://via.placeholder.com/200x200?text=Home"},
    ]
    
    async with AsyncSessionLocal() as db:
        for cat_data in categories:
            category = Category(**cat_data)
            db.add(category)
        await db.commit()
        print("✅ Categories created")

async def init_products():
    """Create sample products"""
    products = [
        # Fruits & Vegetables (category_id: 1)
        {"name": "Fresh Bananas", "price": 40.0, "mrp": 50.0, "category_id": 1, "stock_quantity": 100, "unit": "dozen", "description": "Fresh yellow bananas"},
        {"name": "Red Apples", "price": 120.0, "mrp": 150.0, "category_id": 1, "stock_quantity": 50, "unit": "kg", "description": "Crispy red apples"},
        {"name": "Onions", "price": 30.0, "mrp": 35.0, "category_id": 1, "stock_quantity": 200, "unit": "kg", "description": "Fresh onions"},
        {"name": "Tomatoes", "price": 25.0, "mrp": 30.0, "category_id": 1, "stock_quantity": 150, "unit": "kg", "description": "Red tomatoes"},
        
        # Dairy & Bakery (category_id: 2)
        {"name": "Milk (1L)", "price": 60.0, "mrp": 65.0, "category_id": 2, "stock_quantity": 80, "unit": "liter", "description": "Fresh cow milk"},
        {"name": "Bread", "price": 25.0, "mrp": 30.0, "category_id": 2, "stock_quantity": 40, "unit": "piece", "description": "White bread loaf"},
        {"name": "Butter", "price": 45.0, "mrp": 50.0, "category_id": 2, "stock_quantity": 30, "unit": "piece", "description": "Salted butter"},
        
        # Snacks & Beverages (category_id: 3)
        {"name": "Coca Cola", "price": 40.0, "mrp": 45.0, "category_id": 3, "stock_quantity": 100, "unit": "piece", "description": "Cold drink 500ml"},
        {"name": "Chips", "price": 20.0, "mrp": 25.0, "category_id": 3, "stock_quantity": 60, "unit": "piece", "description": "Potato chips"},
        {"name": "Biscuits", "price": 15.0, "mrp": 20.0, "category_id": 3, "stock_quantity": 80, "unit": "piece", "description": "Cream biscuits"},
    ]
    
    async with AsyncSessionLocal() as db:
        for prod_data in products:
            product = Product(**prod_data)
            db.add(product)
        await db.commit()
        print("✅ Products created")

async def init_delivery_partners():
    """Create sample delivery partners"""
    partners = [
        {
            "firebase_uid": "delivery1_uid",
            "name": "Rahul Kumar",
            "phone": "+919876543210",
            "email": "rahul@delivery.com",
            "status": DeliveryStatus.AVAILABLE
        },
        {
            "firebase_uid": "delivery2_uid", 
            "name": "Amit Singh",
            "phone": "+919876543211",
            "email": "amit@delivery.com",
            "status": DeliveryStatus.AVAILABLE
        }
    ]
    
    async with AsyncSessionLocal() as db:
        for partner_data in partners:
            partner = DeliveryPartner(**partner_data)
            db.add(partner)
        await db.commit()
        print("✅ Delivery partners created")

async def main():
    """Initialize all sample data"""
    print("🚀 Initializing sample data...")
    await init_categories()
    await init_products()
    await init_delivery_partners()
    print("✅ Sample data initialization complete!")

if __name__ == "__main__":
    asyncio.run(main())