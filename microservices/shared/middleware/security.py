from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import logging
from typing import Dict, Any
import redis
import os

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced security headers middleware with sensitive endpoint detection"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            ),
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
            "Server": "GroFast-API"
        }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        for header_name, header_value in self.security_headers.items():
            if header_name == "Strict-Transport-Security":
                if request.url.scheme == "https":
                    response.headers[header_name] = header_value
            else:
                response.headers[header_name] = header_value
        
        # Add cache control for sensitive endpoints
        if self._is_sensitive_endpoint(request.url.path):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint contains sensitive data"""
        sensitive_patterns = ["/auth/", "/admin/", "/orders/", "/cart/", "/delivery/", "/notifications/"]
        return any(path.startswith(pattern) for pattern in sensitive_patterns)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with endpoint-specific limits"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.redis_client = None
        try:
            self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Redis connection established for rate limiting")
        except Exception as e:
            logger.warning(f"Redis unavailable for rate limiting: {e}")
            self.redis_available = False
            self.memory_store = {}
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        if hasattr(request.state, 'user') and request.state.user:
            return f"user:{request.state.user.get('user_id', 'anonymous')}"
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host
        return f"ip:{client_ip}"
    
    def _get_endpoint_limit(self, path: str) -> int:
        """Get rate limit based on endpoint"""
        if path.startswith("/auth/"):
            return 20  # Stricter for auth
        elif path.startswith("/admin/"):
            return 50  # Moderate for admin
        return self.requests_per_minute  # Default
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        identifier = self._get_client_identifier(request)
        limit = self._get_endpoint_limit(request.url.path)
        current_time = int(time.time())
        window_start = current_time - 60
        
        # Check rate limit
        if await self._is_rate_limited(identifier, current_time, window_start, limit):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": limit,
                    "retry_after": 60
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60"
                }
            )
        
        # Record request
        await self._record_request(identifier, current_time)
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        return response
    
    async def _is_rate_limited(self, identifier: str, current_time: int, window_start: int, limit: int) -> bool:
        if self.redis_available:
            try:
                key = f"rate_limit:{identifier}"
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.expire(key, 60)
                results = pipe.execute()
                return results[1] >= limit
            except:
                pass
        
        # Fallback to memory
        if identifier not in self.memory_store:
            self.memory_store[identifier] = []
        
        self.memory_store[identifier] = [
            req_time for req_time in self.memory_store[identifier] 
            if req_time > window_start
        ]
        
        return len(self.memory_store[identifier]) >= limit
    
    async def _record_request(self, identifier: str, current_time: int):
        if self.redis_available:
            try:
                key = f"rate_limit:{identifier}"
                self.redis_client.zadd(key, {str(current_time): current_time})
                return
            except:
                pass
        
        # Fallback to memory
        if identifier not in self.memory_store:
            self.memory_store[identifier] = []
        self.memory_store[identifier].append(current_time)