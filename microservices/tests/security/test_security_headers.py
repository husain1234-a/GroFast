import pytest
import httpx
from fastapi.testclient import TestClient
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from middleware.security import SecurityHeadersMiddleware
from fastapi import FastAPI

@pytest.fixture
def app_with_security():
    """Create test app with security middleware"""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return app

@pytest.fixture
def client(app_with_security):
    """Create test client"""
    return TestClient(app_with_security)

def test_security_headers_present(client):
    """Test that all required security headers are present"""
    response = client.get("/test")
    
    # Check all security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers
    assert "Permissions-Policy" in response.headers
    assert response.headers.get("Server") == "GroFast-API"

def test_csp_header_content(client):
    """Test Content Security Policy header content"""
    response = client.get("/test")
    csp = response.headers.get("Content-Security-Policy")
    
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp

def test_https_only_headers(client):
    """Test HTTPS-only headers are not set for HTTP requests"""
    response = client.get("/test")
    
    # HSTS should not be set for HTTP requests
    assert "Strict-Transport-Security" not in response.headers

if __name__ == "__main__":
    pytest.main([__file__])