#!/usr/bin/env python3
"""Comprehensive API testing script"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_all_endpoints():
    """Test all available API endpoints"""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Blinkit Clone APIs...\n")
        
        tests = [
            ("GET", "/health", None, "Health Check"),
            ("GET", "/", None, "Root Endpoint"),
            ("GET", "/products/categories", None, "Categories"),
            ("GET", "/products", None, "Products"),
            ("GET", "/products?search=apple", None, "Product Search"),
            ("POST", "/auth/google-login", {"google_id_token": "dummy"}, "Google Login (Expected to fail)"),
            ("GET", "/admin/stats?admin_key=admin123", None, "Admin Stats"),
        ]
        
        for method, endpoint, data, description in tests:
            try:
                if method == "GET":
                    response = await client.get(f"{BASE_URL}{endpoint}")
                else:
                    response = await client.post(
                        f"{BASE_URL}{endpoint}", 
                        json=data,
                        headers={"Content-Type": "application/json"}
                    )
                
                status = "✅" if response.status_code < 400 else "❌"
                print(f"{status} {description}: {response.status_code}")
                
                if response.status_code < 400 and len(response.text) < 200:
                    print(f"   Response: {response.text[:100]}...")
                elif response.status_code >= 400:
                    print(f"   Error: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"❌ {description}: Connection Error - {e}")
            
            print()
        
        print("🎯 Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())