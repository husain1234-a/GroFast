#!/usr/bin/env python3
"""Simple API test script"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_endpoints():
    """Test basic API endpoints"""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Blinkit Clone API...")
        
        # Test health check
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test root endpoint
        try:
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("✅ Root endpoint working")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
        
        # Test categories
        try:
            response = await client.get(f"{BASE_URL}/products/categories")
            if response.status_code == 200:
                categories = response.json()
                print(f"✅ Categories endpoint working ({len(categories)} categories)")
            else:
                print(f"❌ Categories failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Categories error: {e}")
        
        # Test products
        try:
            response = await client.get(f"{BASE_URL}/products")
            if response.status_code == 200:
                products = response.json()
                print(f"✅ Products endpoint working ({len(products)} products)")
            else:
                print(f"❌ Products failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Products error: {e}")
        
        print("\n🎯 API testing completed!")

if __name__ == "__main__":
    asyncio.run(test_endpoints())