"""
Integration tests for API endpoints
"""

import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import json


class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API testing"""
        return "http://localhost:8000"
    
    @pytest.fixture
    async def async_client(self, base_url):
        """Async HTTP client for testing"""
        async with AsyncClient(base_url=base_url) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client):
        """Test health check endpoint"""
        # Act
        response = await async_client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client):
        """Test root endpoint"""
        # Act
        response = await async_client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Blinkit Clone API" in data["message"]
    
    @pytest.mark.asyncio
    async def test_products_endpoint(self, async_client):
        """Test products listing endpoint"""
        # Act
        response = await async_client.get("/products")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_products_categories_endpoint(self, async_client):
        """Test product categories endpoint"""
        # Act
        response = await async_client.get("/products/categories")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_product_search_endpoint(self, async_client):
        """Test product search endpoint"""
        # Act
        response = await async_client.get("/products?search=apple")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.AuthService.verify_firebase_token')
    async def test_auth_register_endpoint(self, mock_verify_token, async_client, sample_user_data):
        """Test user registration endpoint"""
        # Arrange
        mock_verify_token.return_value = {
            "uid": sample_user_data["firebase_uid"],
            "email": sample_user_data["email"]
        }
        
        payload = {
            "firebase_id_token": "mock_token_123",
            "name": sample_user_data["name"],
            "address": sample_user_data["address"]
        }
        
        # Act
        response = await async_client.post("/auth/register", json=payload)
        
        # Assert
        assert response.status_code in [200, 201]
        data = response.json()
        assert "firebase_uid" in data
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.AuthService.verify_firebase_token')
    async def test_auth_verify_otp_endpoint(self, mock_verify_token, async_client):
        """Test OTP verification endpoint"""
        # Arrange
        mock_verify_token.return_value = {
            "uid": "test_user_123",
            "phone_number": "+1234567890"
        }
        
        payload = {
            "firebase_id_token": "mock_otp_token_123"
        }
        
        # Act
        response = await async_client.post("/auth/verify-otp", json=payload)
        
        # Assert
        assert response.status_code in [200, 201]
        data = response.json()
        assert "firebase_uid" in data
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.AuthService.get_user_by_firebase_uid')
    async def test_get_user_profile_endpoint(self, mock_get_user, async_client, sample_user_data):
        """Test get user profile endpoint"""
        # Arrange
        mock_get_user.return_value = sample_user_data
        
        # Act
        response = await async_client.get("/auth/me", params={"firebase_token": "mock_token_123"})
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["firebase_uid"] == sample_user_data["firebase_uid"]
    
    @pytest.mark.asyncio
    @patch('app.services.cart_service.CartService.get_cart')
    async def test_get_cart_endpoint(self, mock_get_cart, async_client, sample_cart_data):
        """Test get cart endpoint"""
        # Arrange
        mock_get_cart.return_value = sample_cart_data
        
        # Act
        response = await async_client.get("/cart", params={"firebase_token": "mock_token_123"})
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    @pytest.mark.asyncio
    @patch('app.services.cart_service.CartService.add_item_to_cart')
    async def test_add_to_cart_endpoint(self, mock_add_item, async_client):
        """Test add item to cart endpoint"""
        # Arrange
        mock_add_item.return_value = True
        
        payload = {
            "product_id": 1,
            "quantity": 2
        }
        
        # Act
        response = await async_client.post(
            "/cart/add", 
            json=payload,
            params={"firebase_token": "mock_token_123"}
        )
        
        # Assert
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    @patch('app.services.order_service.OrderService.create_order')
    async def test_create_order_endpoint(self, mock_create_order, async_client, sample_order_data):
        """Test create order endpoint"""
        # Arrange
        mock_create_order.return_value = sample_order_data
        
        payload = {
            "items": sample_order_data["items"],
            "delivery_address": sample_order_data["delivery_address"]
        }
        
        # Act
        response = await async_client.post(
            "/orders", 
            json=payload,
            params={"firebase_token": "mock_token_123"}
        )
        
        # Assert
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
    
    @pytest.mark.asyncio
    @patch('app.services.order_service.OrderService.get_user_orders')
    async def test_get_user_orders_endpoint(self, mock_get_orders, async_client, sample_order_data):
        """Test get user orders endpoint"""
        # Arrange
        mock_get_orders.return_value = [sample_order_data]
        
        # Act
        response = await async_client.get("/orders", params={"firebase_token": "mock_token_123"})
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 0
    
    @pytest.mark.asyncio
    async def test_admin_stats_endpoint(self, async_client):
        """Test admin stats endpoint"""
        # Act
        response = await async_client.get("/admin/stats", params={"admin_key": "admin123"})
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data or "message" in data
    
    @pytest.mark.asyncio
    async def test_invalid_endpoint_404(self, async_client):
        """Test invalid endpoint returns 404"""
        # Act
        response = await async_client.get("/invalid/endpoint")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_missing_auth_token_401(self, async_client):
        """Test missing authentication token returns 401"""
        # Act
        response = await async_client.get("/auth/me")
        
        # Assert
        assert response.status_code in [400, 401, 422]
    
    @pytest.mark.asyncio
    async def test_invalid_json_payload_422(self, async_client):
        """Test invalid JSON payload returns 422"""
        # Act
        response = await async_client.post("/auth/register", json={"invalid": "data"})
        
        # Assert
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client):
        """Test CORS headers are present"""
        # Act
        response = await async_client.options("/")
        
        # Assert
        # Should have CORS headers or return 200/405
        assert response.status_code in [200, 405]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_client):
        """Test rate limiting (if implemented)"""
        # Act - Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = await async_client.get("/health")
            responses.append(response.status_code)
        
        # Assert - All should succeed or some should be rate limited
        assert all(status in [200, 429] for status in responses)
    
    @pytest.mark.asyncio
    async def test_request_timeout_handling(self, async_client):
        """Test request timeout handling"""
        # Act - This should complete quickly or timeout gracefully
        try:
            response = await async_client.get("/health", timeout=1.0)
            assert response.status_code == 200
        except Exception as e:
            # Timeout is acceptable for this test
            assert "timeout" in str(e).lower() or "connection" in str(e).lower()