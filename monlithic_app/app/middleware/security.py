"""
Security middleware for comprehensive web application protection.

This module implements security headers and request/response security processing
to protect against common web vulnerabilities including XSS, clickjacking,
MIME sniffing, and other security threats.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from typing import Callable, Dict, Optional
import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security headers middleware that adds multiple layers
    of protection against common web vulnerabilities.
    
    This middleware automatically adds security headers to all HTTP responses
    to protect against:
    - Cross-Site Scripting (XSS) attacks
    - Clickjacking attacks
    - MIME type sniffing vulnerabilities
    - Content type confusion attacks
    - Referrer information leakage
    - Insecure transport protocols
    
    The middleware is configurable based on environment settings and can be
    customized for different deployment scenarios (development, staging, production).
    
    Attributes:
        security_headers (Dict[str, str]): Default security headers configuration
        csp_policy (str): Content Security Policy configuration
        development_mode (bool): Whether running in development mode
    """
    
    def __init__(self, app, development_mode: bool = False):
        """
        Initialize the security headers middleware.
        
        Args:
            app: The FastAPI application instance
            development_mode (bool): Whether to use development-friendly headers.
                                   In development mode, some restrictions are relaxed
                                   for easier debugging and testing.
        """
        super().__init__(app)
        self.development_mode = development_mode or settings.debug
        self.security_headers = self._build_security_headers()
        self.csp_policy = self._build_csp