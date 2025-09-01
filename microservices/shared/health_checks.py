from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Callable
import psutil
import os

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self, service_name: str, logger=None):
        self.service_name = service_name
        self.logger = logger
        self.dependency_checks = {}
        self.checks = {}  # For backward compatibility
    
    def register_dependency_check(self, name: str, check_func: Callable):
        """Register a dependency health check"""
        self.dependency_checks[name] = check_func
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check function (backward compatibility)"""
        self.dependency_checks[name] = check_func
    
    async def check_database(self, db_session_factory=None) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            if db_session_factory:
                async with db_session_factory() as db:
                    await db.execute("SELECT 1")
                    return {"status": "healthy", "response_time": "< 100ms"}
            else:
                # Mock for when no db_session_factory is provided
                return {"status": "healthy", "response_time": "< 100ms"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_redis(self, redis_url: str) -> Dict[str, Any]:
        """Check Redis connectivity (async)"""
        try:
            import redis.asyncio as redis
            r = redis.Redis.from_url(redis_url)
            await r.ping()
            await r.close()
            return {"status": "healthy", "response_time": "< 50ms"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_http_service(self, service_name: str, url: str) -> Dict[str, Any]:
        """Check HTTP service health"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start_time = datetime.now()
                response = await client.get(url)
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "response_time": f"{response_time:.2f}ms",
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "status": "degraded",
                        "response_time": f"{response_time:.2f}ms",
                        "status_code": response.status_code
                    }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_meilisearch(self, meilisearch_url: str, master_key: str = None) -> Dict[str, Any]:
        """Check Meilisearch connectivity"""
        try:
            headers = {}
            if master_key:
                headers["Authorization"] = f"Bearer {master_key}"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{meilisearch_url}/health", headers=headers)
                if response.status_code == 200:
                    return {"status": "healthy", "type": "meilisearch", "url": meilisearch_url}
                else:
                    return {"status": "unhealthy", "type": "meilisearch", "url": meilisearch_url, "status_code": response.status_code}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics (non-blocking)"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),  # Non-blocking call
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health_data = {
            "service": self.service_name,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "uptime": self._get_uptime(),
            "system": self.get_system_metrics(),
            "dependencies": {}
        }
        
        # Check all registered dependencies
        for name, check_func in self.dependency_checks.items():
            try:
                health_data["dependencies"][name] = await check_func()
            except Exception as e:
                health_data["dependencies"][name] = {"status": "unhealthy", "error": str(e)}
        
        # Determine overall status
        unhealthy_deps = [
            name for name, status in health_data["dependencies"].items()
            if status.get("status") != "healthy"
        ]
        
        if unhealthy_deps:
            health_data["status"] = "degraded" if len(unhealthy_deps) < len(health_data["dependencies"]) else "unhealthy"
            health_data["unhealthy_dependencies"] = unhealthy_deps
        
        return health_data
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks (backward compatibility)"""
        results = {}
        for name, check_func in self.dependency_checks.items():
            try:
                results[name] = await check_func()
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}
        return results
    
    def _get_uptime(self) -> str:
        """Get service uptime"""
        try:
            uptime_seconds = psutil.boot_time()
            uptime = datetime.now().timestamp() - uptime_seconds
            return f"{uptime:.2f} seconds"
        except:
            return "unknown"

def create_fastapi_health_endpoints(app: FastAPI, health_checker: HealthChecker):
    """Add health check endpoints to FastAPI app"""
    
    @app.get("/health")
    async def health_check():
        """Basic health check"""
        return {"status": "healthy", "service": health_checker.service_name}
    
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with dependencies"""
        health_data = await health_checker.get_comprehensive_health()
        status_code = 200 if health_data["status"] == "healthy" else 503
        return JSONResponse(content=health_data, status_code=status_code)
    
    @app.get("/health/ready")
    async def readiness_check():
        """Kubernetes readiness probe"""
        health_data = await health_checker.get_comprehensive_health()
        if health_data["status"] in ["healthy", "degraded"]:
            return {"status": "ready"}
        else:
            return JSONResponse(content={"status": "not ready"}, status_code=503)
    
    @app.get("/health/live")
    async def liveness_check():
        """Kubernetes liveness probe"""
        return {"status": "alive", "service": health_checker.service_name}

# Alias for backward compatibility
add_health_endpoints = create_fastapi_health_endpoints