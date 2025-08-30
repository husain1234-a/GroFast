"""
Test configuration and fixtures for the Blinkit Clone application
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

# Test data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "firebase_uid": "test_user_123",
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+1234567890",
        "address": "123 Test Street, Test City",
        "fcm_token": "test_fcm_token_123"
    }

@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        "id": 1,
        "name": "Test Product",
        "description": "A test product for unit testing",
        "price": 29.99,
        "category": "Test Category",
        "stock": 100,
        "image_url": "https://example.com/test-product.jpg",
        "is_available": True
    }

@pytest.fixture
def sample_cart_data():
    """Sample cart data for testing"""
    return {
        "user_id": "test_user_123",
        "items": [
            {
                "product_id": 1,
                "quantity": 2,
                "price": 29.99
            },
            {
                "product_id": 2,
                "quantity": 1,
                "price": 15.50
            }
        ],
        "total": 75.48
    }

@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "id": "order_123",
        "user_id": "test_user_123",
        "items": [
            {
                "product_id": 1,
                "quantity": 2,
                "price": 29.99
            }
        ],
        "total": 59.98,
        "status": "pending",
        "delivery_address": "123 Test Street, Test City",
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def mock_firebase_auth():
    """Mock Firebase authentication"""
    mock = Mock()
    mock.verify_id_token = Mock(return_value={
        "uid": "test_user_123",
        "email": "test@example.com",
        "name": "Test User"
    })
    return mock

@pytest.fixture
def mock_database():
    """Mock database connection"""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.fetch = AsyncMock()
    mock.fetchrow = AsyncMock()
    return mock

@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    mock = AsyncMock()
    mock.get = AsyncMock()
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.exists = AsyncMock()
    return mock

@pytest.fixture
def mock_notification_service():
    """Mock notification service"""
    mock = AsyncMock()
    mock.send_push_notification = AsyncMock(return_value=True)
    mock.send_email = AsyncMock(return_value=True)
    mock.send_sms = AsyncMock(return_value=True)
    return mock

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for inter-service communication"""
    mock = AsyncMock()
    mock.get = AsyncMock()
    mock.post = AsyncMock()
    mock.put = AsyncMock()
    mock.delete = AsyncMock()
    return mock

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()