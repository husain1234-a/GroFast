"""
Enhanced Health Check Utilities for Microservices
Provides comprehensive health checking capabilities including dependency monitoring.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import aiohttp
import asyncpg
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

@dataclass
class HealthCheckResult:
    """Result of a health check operation"""
    name: str
    status: str  # "healthy", "unhealthy", "degraded"
    response_time_ms: float
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

class HealthChecker:
    """Comprehensive health checker for microservices"""
    
    def __init__(self, service_name: str, logger: Optional[logging.Logger] = None):
        self.service_name = service_name
        self.logger = logger or logging.getLogger(__name__)
        self.checks: Dict[str, Callable] = {}
        self.dependency_checks: Dict[str, Callable] = {}
    
    def register_check(self, name: str, check_func: Callable):
        """Register a custom health check"""
        self.checks[name] = check_func
    
    def register_dependency_check(self, name: str, check_func: Callable):
        """Register a dependency health check"""
        self.dependency_checks[name] = check_func
    
    async def check_database(self, db_session_factory, query: str = "SELECT 1") -> HealthCheckResult:
        """Check database connectivity"""
        start_time = time.time()
        
        try:
            async with db_session_factory() as session:
                await session.execute(text(query))
                response_time = (time.time() - start_time) * 1000
                
                return HealthCheckResult(
                    name="database",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"query": query}
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Database health check failed: {e}")
            
            return HealthCheckResult(
                name="database",
                status="unhealthy",
                response_time_ms=response_time,
                error=str(e),
                details={"query": query}
            )
    
    async def check_redis(self, redis_url: str) -> HealthCheckResult:
        """Check Redis connectivity"""
        start_time = time.time()
        
        try:
            redis_client = redis.from_url(redis_url)
            await redis_client.ping()
            await redis_client.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name="redis",
                status="healthy",
                response_time_ms=response_time,
                details={"redis_url": redis_url.split('@')[-1]}  # Hide credentials
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Redis health check failed: {e}")
            
            return HealthCheckResult(
                name="redis",
                status="unhealthy",
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def check_http_service(self, name: str, url: str, timeout: int = 5) -> HealthCheckResult:
        """Check HTTP service availability"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return HealthCheckResult(
                            name=name,
                            status="healthy",
                            response_time_ms=response_time,
                            details={"url": url, "status_code": response.status}
                        )
                    else:
                        return HealthCheckResult(
                            name=name,
                            status="degraded",
                            response_time_ms=response_time,
                            details={"url": url, "status_code": response.status},
                            error=f"HTTP {response.status}"
                        )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"HTTP service check failed for {name}: {e}")
            
            return HealthCheckResult(
                name=name,
                status="unhealthy",
                response_time_ms=response_time,
                error=str(e),
                details={"url": url}
            )
    
    async def check_meilisearch(self, url: str, master_key: str = None) -> HealthCheckResult:
        """Check Meilisearch availability"""
        start_time = time.time()
        
        try:
            headers = {}
            if master_key:
                headers["Authorization"] = f"Bearer {master_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return HealthCheckResult(
                            name="meilisearch",
                            status="healthy",
                            response_time_ms=response_time,
                            details={"url": url, "status": data.get("status")}
                        )
                    else:
                        return HealthCheckResult(
                            name="meilisearch",
                            status="unhealthy",
                            response_time_ms=response_time,
                            error=f"HTTP {response.status}"
                        )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Meilisearch health check failed: {e}")
            
            return HealthCheckResult(
                name="meilisearch",
                status="unhealthy",
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {},
            "dependencies": {}
        }
        
        # Run basic checks
        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results["checks"][name] = asdict(result)
                
                if result.status != "healthy":
                    results["status"] = "degraded"
            except Exception as e:
                self.logger.error(f"Health check {name} failed: {e}")
                results["checks"][name] = {
                    "name": name,
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                results["status"] = "degraded"
        
        # Run dependency checks
        for name, check_func in self.dependency_checks.items():
            try:
                result = await check_func()
                results["dependencies"][name] = asdict(result)
                
                if result.status == "unhealthy":
                    results["status"] = "degraded"
            except Exception as e:
                self.logger.error(f"Dependency check {name} failed: {e}")
                results["dependencies"][name] = {
                    "name": name,
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                results["status"] = "degraded"
        
        return results
    
    async def get_basic_health(self) -> Dict[str, Any]:
        """Get basic health status without dependency checks"""
        return {
            "service": self.service_name,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }

def create_fastapi_health_endpoints(app, health_checker: HealthChecker):
    """Create FastAPI health check endpoints"""
    
    @app.get("/health")
    async def basic_health():
        """Basic health check endpoint"""
        return await health_checker.get_basic_health()
    
    @app.get("/health/detailed")
    async def detailed_health():
        """Detailed health check with dependencies"""
        result = await health_checker.run_all_checks()
        
        # Return appropriate HTTP status
        if result["status"] == "healthy":
            return result
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=result)
    
    @app.get("/health/ready")
    async def readiness_check():
        """Readiness check - service is ready to handle requests"""
        result = await health_checker.run_all_checks()
        
        # Service is ready if it's healthy or degraded (but not completely down)
        if result["status"] in ["healthy", "degraded"]:
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503, 
                detail={"status": "not_ready", "timestamp": datetime.utcnow().isoformat()}
            )
    
    @app.get("/health/live")
    async def liveness_check():
        """Liveness check - service is alive"""
        return {
            "status": "alive",
            "service": health_checker.service_name,
            "timestamp": datetime.utcnow().isoformat()
        }

# Utility functions for common health check patterns
async def check_postgres_health(database_url: str) -> HealthCheckResult:
    """Standalone PostgreSQL health check"""
    start_time = time.time()
    
    try:
        conn = await asyncpg.connect(database_url)
        await conn.execute("SELECT 1")
        await conn.close()
        
        response_time = (time.time() - start_time) * 1000
        
        return HealthCheckResult(
            name="postgresql",
            status="healthy",
            response_time_ms=response_time
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return HealthCheckResult(
            name="postgresql",
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )

async def check_service_dependencies(dependencies: Dict[str, str]) -> Dict[str, HealthCheckResult]:
    """Check multiple service dependencies concurrently"""
    tasks = []
    
    for name, url in dependencies.items():
        if url.startswith("http"):
            task = check_http_service_health(name, f"{url}/health")
        else:
            # Assume it's a database URL
            task = check_postgres_health(url)
        
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    dependency_results = {}
    for i, (name, _) in enumerate(dependencies.items()):
        result = results[i]
        if isinstance(result, Exception):
            dependency_results[name] = HealthCheckResult(
                name=name,
                status="unhealthy",
                response_time_ms=0,
                error=str(result)
            )
        else:
            dependency_results[name] = result
    
    return dependency_results

async def check_http_service_health(name: str, url: str) -> HealthCheckResult:
    """Standalone HTTP service health check"""
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(url) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    return HealthCheckResult(
                        name=name,
                        status="healthy",
                        response_time_ms=response_time
                    )
                else:
                    return HealthCheckResult(
                        name=name,
                        status="degraded",
                        response_time_ms=response_time,
                        error=f"HTTP {response.status}"
                    )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return HealthCheckResult(
            name=name,
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )