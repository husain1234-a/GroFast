#!/usr/bin/env python3
"""
Setup test data for the application
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.config.database import engine, AsyncSessionLocal
from app.models.product import Category, Product
from app.models.user import User

async def setup_database():
    """Create tables and add test data"""
    
    try:
        # Create all tables
        from app.config.database import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("Tables created successfully!")
        
        # Add test data
        async with AsyncSessionLocal() as session:
            # Check if categories exist
            result = await session.execute(text("SELECT COUNT(*) FROM categories"))
            category_count = result.scalar()
            
            if category_count == 0:
                print("Adding test categories...")
                categories = [
                    Category(name="Fruits & Vegetables", image_url="https://example.com/fruits.jpg"),
                    Category(name="Dairy & Bakery", image_url="https://example.com/dairy.jpg"),
                    Category(name="Snacks & Beverages", image_url="https://example.com/snacks.jpg"),
                    Category(name="Personal Care", image_url="https://example.com/care.jpg"),
                ]
                
                for cat in categories:
                    session.add(cat)
                
                await session.commit()
                print(f"Added {len(categories)} categories")
            
            # Check if products exist
            result = await session.execute(text("SELECT COUNT(*) FROM products"))
            product_count = result.scalar()
            
            if product_count == 0:
                print("Adding test products...")
                products = [
                    Product(name="Fresh Bananas", description="Fresh yellow bananas", price=40.0, mrp=50.0, category_id=1, stock_quantity=100, unit="kg"),
                    Product(name="Red Apples", description="Fresh red apples", price=120.0, mrp=150.0, category_id=1, stock_quantity=50, unit="kg"),
                    Product(name="Fresh Milk", description="Full cream milk", price=60.0, mrp=65.0, category_id=2, stock_quantity=30, unit="liter"),
                    Product(name="White Bread", description="Fresh white bread", price=25.0, mrp=30.0, category_id=2, stock_quantity=20, unit="piece"),
                    Product(name="Coca Cola", description="Cold drink", price=40.0, mrp=45.0, category_id=3, stock_quantity=100, unit="piece"),
                ]
                
                for prod in products:
                    session.add(prod)
                
                await session.commit()
                print(f"Added {len(products)} products")
            
            print("Database setup completed!")
            
    except Exception as e:
        print(f"Error setting up database: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_database())