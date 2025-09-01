#!/usr/bin/env python3
"""
Health Check Test Script
Tests all microservice health endpoints to ensure they're working correctly
"""

import asyncio
import aiohttp
import sys
import time
from typing import Dict, List, Tuple

# Service endpoints to test
SERVICES = {
    "api-gateway": "http://localhost:8000",
    "auth-service": "http://localhost:8001", 
    "product-service": "http://localhost:8002",
    "cart-service": "http://localhost:8003",
    "order-service": "http://localhost:8004",
    "delivery-service": "http://localhost:8005",
    "notification-service": "http://localhost:8006"
}

HEALTH_ENDPOINTS = [
    "/health",           # Basic health check
    "/health/detailed",  # Detailed health with dependencies
    "/health/ready",     # Readiness check
    "/health/live"       # Liveness check
]

async def test_health_endpoint(session: aiohttp.ClientSession, service_name: str, base_url: str, endpoint: str) -> Tuple[str, str, int, str]:
    """Test a single health endpoint"""
    url = f"{base_url}{endpoint}"
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            status = response.status
            text = await response.text()
            
            if status in [200, 503]:  # 503 is acceptable for degraded services
                return (service_name, endpoint, status, "✅ OK")
            else:
                return (service_name, endpoint, status, f"❌ Unexpected status: {status}")
                
    except asyncio.TimeoutError:
        return (service_name, endpoint, 0, "❌ Timeout")
    except aiohttp.ClientConnectorError:
        return (service_name, endpoint, 0, "❌ Connection refused")
    except Exception as e:
        return (service_name, endpoint, 0, f"❌ Error: {str(e)}")

async def test_all_health_checks() -> Dict[str, List[Tuple[str, int, str]]]:
    """Test all health endpoints for all services"""
    results = {}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for service_name, base_url in SERVICES.items():
            results[service_name] = []
            
            for endpoint in HEALTH_ENDPOINTS:
                task = test_health_endpoint(session, service_name, base_url, endpoint)
                tasks.append(task)
        
        # Execute all tests concurrently
        test_results = await asyncio.gather(*tasks)
        
        # Group results by service
        for service_name, endpoint, status, message in test_results:
            results[service_name].append((endpoint, status, message))
    
    return results

def print_results(results: Dict[str, List[Tuple[str, int, str]]]):
    """Print test results in a formatted way"""
    print("\n" + "="*80)
    print("MICROSERVICES HEALTH CHECK TEST RESULTS")
    print("="*80)
    
    total_tests = 0
    passed_tests = 0
    
    for service_name, service_results in results.items():
        print(f"\n🔧 {service_name.upper()}")
        print("-" * 40)
        
        for endpoint, status, message in service_results:
            total_tests += 1
            if "✅" in message:
                passed_tests += 1
            
            status_str = f"[{status}]" if status > 0 else "[---]"
            print(f"  {endpoint:<20} {status_str:<6} {message}")
    
    print("\n" + "="*80)
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 All health checks are working correctly!")
        return True
    else:
        print("⚠️  Some health checks failed. Check the services and try again.")
        return False

async def wait_for_services(max_wait_time: int = 120):
    """Wait for services to become available"""
    print("⏳ Waiting for services to start...")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            async with aiohttp.ClientSession() as session:
                # Test a simple endpoint to see if any service is up
                async with session.get("http://localhost:8000/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status in [200, 503]:
                        print("✅ Services are responding!")
                        return True
        except:
            pass
        
        await asyncio.sleep(5)
        print(f"⏳ Still waiting... ({int(time.time() - start_time)}s elapsed)")
    
    print("❌ Timeout waiting for services to start")
    return False

async def main():
    """Main test function"""
    print("🚀 Starting Microservices Health Check Tests")
    
    # Wait for services to be available
    if not await wait_for_services():
        sys.exit(1)
    
    # Run health check tests
    results = await test_all_health_checks()
    
    # Print results
    success = print_results(results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())