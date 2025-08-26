import redis
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis_client = redis.from_url(settings.redis_url)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        try:
            current_requests = self.redis_client.get(key)
            if current_requests is None:
                self.redis_client.setex(key, 60, 1)
            else:
                current_requests = int(current_requests)
                if current_requests >= 100:  # 100 requests per minute
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"}
                    )
                self.redis_client.incr(key)
        except Exception:
            pass  # Continue if Redis is unavailable
        
        response = await call_next(request)
        return response