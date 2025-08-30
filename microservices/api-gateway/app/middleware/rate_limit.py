import redis
import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        try:
            self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Redis connection established for rate limiting")
        except Exception as e:
            logger.warning(f"Redis unavailable for rate limiting: {e}")
            self.redis_available = False
            # Fallback to in-memory rate limiting
            self.memory_store = {}
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from auth middleware
        if hasattr(request.state, 'user') and request.state.user:
            return f"user:{request.state.user.get('user_id', 'anonymous')}"
        
        # Fallback to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host
        
        return f"ip:{client_ip}"
    
    def _check_rate_limit_redis(self, identifier: str, limit: int = 100, window: int = 60) -> tuple[bool, dict]:
        """Check rate limit using Redis sliding window"""
        try:
            current_time = time.time()
            window_start = current_time - window
            
            # Use Redis sorted set for sliding window
            key = f"rate_limit:{identifier}"
            
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_count = self.redis_client.zcard(key)
            
            if current_count >= limit:
                # Get time until reset
                oldest_request = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    reset_time = int(oldest_request[0][1] + window - current_time)
                else:
                    reset_time = window
                
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": reset_time,
                    "retry_after": reset_time
                }
            
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, window)
            
            return True, {
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset": window
            }
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            return True, {"limit": limit, "remaining": limit, "reset": window}
    
    def _check_rate_limit_memory(self, identifier: str, limit: int = 100, window: int = 60) -> tuple[bool, dict]:
        """Fallback in-memory rate limiting"""
        current_time = time.time()
        
        if identifier not in self.memory_store:
            self.memory_store[identifier] = []
        
        # Clean old entries
        self.memory_store[identifier] = [
            timestamp for timestamp in self.memory_store[identifier]
            if current_time - timestamp < window
        ]
        
        current_count = len(self.memory_store[identifier])
        
        if current_count >= limit:
            oldest_request = min(self.memory_store[identifier])
            reset_time = int(oldest_request + window - current_time)
            
            return False, {
                "limit": limit,
                "remaining": 0,
                "reset": reset_time,
                "retry_after": reset_time
            }
        
        # Add current request
        self.memory_store[identifier].append(current_time)
        
        return True, {
            "limit": limit,
            "remaining": limit - current_count - 1,
            "reset": window
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        identifier = self._get_client_identifier(request)
        
        # Different limits for different endpoints
        if request.url.path.startswith("/auth/"):
            limit = 20  # Stricter limit for auth endpoints
        elif request.url.path.startswith("/admin/"):
            limit = 50  # Moderate limit for admin
        else:
            limit = 100  # Default limit
        
        # Check rate limit
        if self.redis_available:
            allowed, info = self._check_rate_limit_redis(identifier, limit)
        else:
            allowed, info = self._check_rate_limit_memory(identifier, limit)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": info["limit"],
                    "retry_after": info.get("retry_after", 60)
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info.get("retry_after", 60))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        return response