#!/usr/bin/env python3
"""
Fix database schema by adding missing columns to users table
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.config.database import engine

async def fix_database_schema():
    """Add missing columns to users table"""
    
    # SQL commands to add missing columns
    alter_commands = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(100);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS fcm_token TEXT;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS address TEXT;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS latitude VARCHAR(20);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS longitude VARCHAR(20);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
    ]
    
    try:
        async with engine.begin() as conn:
            print("Checking current users table schema...")
            
            # Check current columns
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """))
            
            current_columns = result.fetchall()
            print("Current columns:")
            for col in current_columns:
                print(f"  {col[0]}: {col[1]}")
            
            print("\nAdding missing columns...")
            
            # Execute alter commands
            for command in alter_commands:
                try:
                    await conn.execute(text(command))
                    print(f"OK Executed: {command}")
                except Exception as e:
                    print(f"WARNING: {command} - {e}")
            
            print("\nChecking updated schema...")
            
            # Check updated columns
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """))
            
            updated_columns = result.fetchall()
            print("Updated columns:")
            for col in updated_columns:
                print(f"  {col[0]}: {col[1]}")
            
            print("\nOK Database schema updated successfully!")
            
    except Exception as e:
        print(f"ERROR updating database schema: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_database_schema())