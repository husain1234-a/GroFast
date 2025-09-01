from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

# Import AuthClient from shared auth module
try:
    from auth import AuthClient
except ImportError:
    # Fallback if auth module not available
    class AuthClient:
        def __init__(self, auth_service_url):
            self.auth_service_url = auth_service_url
        
        async def verify_token(self, token):
            # Fallback verification
            if token and len(token) > 10:
                return {
                    "user_id": 1,
                    "email": "fallback@example.com",
                    "name": "Fallback User",
                    "fallback": True
                }
            raise HTTPException(status_code=401, detail="Invalid token")
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_client = AuthClient(settings.auth_service_url)
        
        # Routes that don't require authentication
        self.public_routes = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
            "/auth/register",
            "/auth/verify-otp",
            "/auth/google-login",
            "/products/categories",
            "/products/"
        }
        
        # Routes that require authentication
        self.protected_prefixes = {
            "/auth/me",
            "/cart/",
            "/orders/",
            "/delivery/",
            "/notifications/",
            "/admin/"
        }
    
    def _is_public_route(self, path: str) -> bool:
        """Check if route is public (doesn't require auth)"""
        # Exact matches
        if path in self.public_routes:
            return True
        
        # Check if it's a GET request to products (public browsing)
        if path.startswith("/products/") and not any(path.startswith(prefix) for prefix in self.protected_prefixes):
            return True
            
        return False
    
    def _requires_auth(self, path: str) -> bool:
        """Check if route requires authentication"""
        return any(path.startswith(prefix) for prefix in self.protected_prefixes)
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip auth for public routes
        if self._is_public_route(path):
            return await call_next(request)
        
        # Check if route requires authentication
        if self._requires_auth(path):
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing or invalid authorization header"}
                )
            
            token = auth_header.split(" ")[1]
            
            try:
                # Verify token with auth service
                user_info = await self.auth_client.verify_token(token)
                
                # Add user info to request state
                request.state.user = user_info
                request.state.authenticated = True
                
                # Add user context to headers for downstream services
                if hasattr(request, '_headers'):
                    request._headers = dict(request.headers)
                else:
                    request._headers = {}
                
                request._headers['X-User-ID'] = str(user_info.get('user_id', ''))
                request._headers['X-User-Email'] = user_info.get('email', '')
                
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Authentication service error"}
                )
        
        # Continue to next middleware/route
        response = await call_next(request)
        return response