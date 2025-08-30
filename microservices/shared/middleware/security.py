from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from typing import Dict, Any
import redis
import os

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers to all responses"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
            
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis backend"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.redis_client = None
        try:
            self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        except:
            pass  # Fallback to in-memory if Redis unavailable
        self.memory_store = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = int(time.time())
        window_start = current_time - 60  # 1 minute window
        
        # Check rate limit
        if await self._is_rate_limited(client_ip, current_time, window_start):
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded. Try again later."}
            )
        
        # Record request
        await self._record_request(client_ip, current_time)
        
        response = await call_next(request)
        return response
    
    async def _is_rate_limited(self, client_ip: str, current_time: int, window_start: int) -> bool:
        if self.redis_client:
            try:
                key = f"rate_limit:{client_ip}"
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.expire(key, 60)
                results = pipe.execute()
                return results[1] >= self.requests_per_minute
            except:
                pass
        
        # Fallback to memory
        if client_ip not in self.memory_store:
            self.memory_store[client_ip] = []
        
        # Clean old requests
        self.memory_store[client_ip] = [
            req_time for req_time in self.memory_store[client_ip] 
            if req_time > window_start
        ]
        
        return len(self.memory_store[client_ip]) >= self.requests_per_minute
    
    async def _record_request(self, client_ip: str, current_time: int):
        if self.redis_client:
            try:
                key = f"rate_limit:{client_ip}"
                self.redis_client.zadd(key, {str(current_time): current_time})
                return
            except:
                pass
        
        # Fallback to memory
        if client_ip not in self.memory_store:
            self.memory_store[client_ip] = []
        self.memory_store[client_ip].append(current_time)