"""
Request Validation Middleware
Handles request size limits, content type validation, and input sanitization
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and sanitization"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Configuration
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.max_json_size = 1 * 1024 * 1024      # 1MB for JSON
        self.max_file_size = 5 * 1024 * 1024      # 5MB for files
        
        # Allowed content types
        self.allowed_content_types = {
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain"
        }
        
        # XSS patterns to detect and sanitize
        self.xss_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),
            re.compile(r'<iframe[^>]*>.*?</iframe>', re.IGNORECASE | re.DOTALL),
            re.compile(r'<object[^>]*>.*?</object>', re.IGNORECASE | re.DOTALL),
            re.compile(r'<embed[^>]*>', re.IGNORECASE),
            re.compile(r'<link[^>]*>', re.IGNORECASE),
            re.compile(r'<meta[^>]*>', re.IGNORECASE),
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            re.compile(r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b', re.IGNORECASE),
            re.compile(r'[\'";]', re.IGNORECASE),
            re.compile(r'--', re.IGNORECASE),
            re.compile(r'/\*.*?\*/', re.IGNORECASE | re.DOTALL),
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Validate and sanitize requests"""
        
        # Skip validation for health checks and static content
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        try:
            # Check request size
            content_length = request.headers.get("content-length")
            if content_length:
                size = int(content_length)
                if size > self.max_request_size:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request too large. Maximum size: {self.max_request_size} bytes",
                            "error_code": "REQUEST_TOO_LARGE"
                        }
                    )
            
            # Validate content type for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "").split(";")[0].strip()
                
                if content_type and not any(ct in content_type for ct in self.allowed_content_types):
                    return JSONResponse(
                        status_code=415,
                        content={
                            "detail": f"Unsupported content type: {content_type}",
                            "error_code": "UNSUPPORTED_MEDIA_TYPE"
                        }
                    )
                
                # Additional size check for JSON
                if content_type == "application/json" and content_length:
                    if int(content_length) > self.max_json_size:
                        return JSONResponse(
                            status_code=413,
                            content={
                                "detail": f"JSON payload too large. Maximum size: {self.max_json_size} bytes",
                                "error_code": "JSON_TOO_LARGE"
                            }
                        )
            
            # Validate and sanitize request body for JSON requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    # Read and validate JSON body
                    body = await request.body()
                    if body:
                        try:
                            json_data = json.loads(body)
                            sanitized_data = self._sanitize_json_data(json_data)
                            
                            # Replace request body with sanitized data
                            sanitized_body = json.dumps(sanitized_data).encode()
                            
                            # Create new request with sanitized body
                            async def receive():
                                return {"type": "http.request", "body": sanitized_body}
                            
                            request._receive = receive
                            
                        except json.JSONDecodeError:
                            return JSONResponse(
                                status_code=400,
                                content={
                                    "detail": "Invalid JSON format",
                                    "error_code": "INVALID_JSON"
                                }
                            )
            
            # Validate query parameters
            for param_name, param_value in request.query_params.items():
                if self._contains_malicious_content(param_value):
                    # Sanitize log data to prevent log injection
                    safe_param = param_name.replace('\n', '').replace('\r', '')
                    safe_value = str(param_value).replace('\n', '').replace('\r', '')[:100]
                    logger.warning(f"Malicious content detected in query parameter '{safe_param}': {safe_value}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": f"Invalid content in parameter: {param_name}",
                            "error_code": "MALICIOUS_CONTENT"
                        }
                    )
            
            # Validate path parameters
            if self._contains_malicious_content(str(request.url.path)):
                # Sanitize log data to prevent log injection
                safe_path = str(request.url.path).replace('\n', '').replace('\r', '')
                logger.warning(f"Malicious content detected in path: {safe_path}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Invalid path format",
                        "error_code": "MALICIOUS_PATH"
                    }
                )
            
            # Continue to next middleware/route
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Request validation failed",
                    "error_code": "VALIDATION_ERROR"
                }
            )
    
    def _sanitize_json_data(self, data: Any) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(data, dict):
            return {key: self._sanitize_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string content"""
        if not isinstance(text, str):
            return text
        
        # Remove XSS patterns
        sanitized = text
        for pattern in self.xss_patterns:
            sanitized = pattern.sub('', sanitized)
        
        # Basic HTML entity encoding for remaining < and >
        sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')
        
        return sanitized.strip()
    
    def _contains_malicious_content(self, text: str) -> bool:
        """Check if text contains malicious patterns"""
        if not isinstance(text, str):
            return False
        
        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if pattern.search(text):
                return True
        
        # Check for SQL injection patterns (basic detection)
        for pattern in self.sql_patterns:
            if pattern.search(text):
                return True
        
        # Check for path traversal
        if '../' in text or '..\\' in text:
            return True
        
        # Check for null bytes
        if '\x00' in text:
            return True
        
        return False