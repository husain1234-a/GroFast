"""
Security Headers Middleware
Adds security headers to all responses
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Security headers configuration
        self.security_headers = {
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            ),
            
            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            
            # Server identification
            "Server": "Blinkit-API-Gateway"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        for header_name, header_value in self.security_headers.items():
            # Only add HSTS for HTTPS requests
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
        sensitive_patterns = [
            "/auth/",
            "/admin/",
            "/orders/",
            "/cart/",
            "/delivery/",
            "/notifications/"
        ]
        
        return any(path.startswith(pattern) for pattern in sensitive_patterns)