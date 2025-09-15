#!/usr/bin/env python3
"""
Test database connectivity and performance
"""
import asyncio
import sys
import os
import time

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.config.database import engine

async def test_database():
    """Test database connectivity and performance"""
    
    try:
        print("Testing database connection...")
        start_time = time.time()
        
        async with engine.begin() as conn:
            # Simple connectivity test
            result = await conn.execute(text("SELECT 1 as test"))
            test_result = result.scalar()
            
            connection_time = time.time() - start_time
            print(f"Connection successful! Test query returned: {test_result}")
            print(f"Connection time: {connection_time:.2f} seconds")
            
            # Test users table
            start_time = time.time()
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            query_time = time.time() - start_time
            
            print(f"Users table has {user_count} records")
            print(f"Query time: {query_time:.2f} seconds")
            
            # Test if tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            print(f"Available tables: {[t[0] for t in tables]}")
            
    except Exception as e:
        print(f"Database test failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_database())