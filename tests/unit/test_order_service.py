"""
Unit tests for Order Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.order_service import OrderService
from app.models.order import Order
from datetime import datetime


class TestOrderService:
    """Test cases for OrderService"""
    
    @pytest.fixture
    def order_service(self, mock_database, mock_notification_service):
        """Create OrderService instance with mocked dependencies"""
        service = OrderService()
        service.db = mock_database
        service.notification_service = mock_notification_service
        return service
    
    @pytest.mark.asyncio
    async def test_create_order_success(self, order_service, mock_database, sample_order_data, mock_notification_service):
        """Test successful order creation"""
        # Arrange
        order_data = sample_order_data.copy()
        order_data["id"] = "new_order_123"
        mock_database.fetchrow.return_value = order_data
        mock_database.execute.return_value = None
        
        # Act
        result = await order_service.create_order(
            user_id=order_data["user_id"],
            items=order_data["items"],
            delivery_address=order_data["delivery_address"]
        )
        
        # Assert
        assert result is not None
        assert result["id"] == "new_order_123"
        assert result["status"] == "pending"
        mock_database.execute.assert_called()
        mock_notification_service.send_push_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_order_by_id(self, order_service, mock_database, sample_order_data):
        """Test getting order by ID"""
        # Arrange
        order_id = sample_order_data["id"]
        mock_database.fetchrow.return_value = sample_order_data
        
        # Act
        result = await order_service.get_order_by_id(order_id)
        
        # Assert
        assert result == sample_order_data
        mock_database.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_order_by_id_not_found(self, order_service, mock_database):
        """Test getting non-existent order"""
        # Arrange
        order_id = "non_existent_order"
        mock_database.fetchrow.return_value = None
        
        # Act
        result = await order_service.get_order_by_id(order_id)
        
        # Assert
        assert result is None
        mock_database.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_orders(self, order_service, mock_database, sample_order_data):
        """Test getting all orders for a user"""
        # Arrange
        user_id = sample_order_data["user_id"]
        orders = [sample_order_data, {**sample_order_data, "id": "order_456"}]
        mock_database.fetch.return_value = orders
        
        # Act
        result = await order_service.get_user_orders(user_id)
        
        # Assert
        assert len(result) == 2
        assert all(order["user_id"] == user_id for order in result)
        mock_database.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_order_status_success(self, order_service, mock_database, mock_notification_service):
        """Test successful order status update"""
        # Arrange
        order_id = "order_123"
        new_status = "confirmed"
        updated_order = {"id": order_id, "status": new_status, "user_id": "test_user_123"}
        mock_database.fetchrow.return_value = updated_order
        mock_database.execute.return_value = None
        
        # Act
        result = await order_service.update_order_status(order_id, new_status)
        
        # Assert
        assert result["status"] == new_status
        mock_database.execute.assert_called_once()
        mock_notification_service.send_push_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, order_service, mock_database, mock_notification_service):
        """Test successful order cancellation"""
        # Arrange
        order_id = "order_123"
        user_id = "test_user_123"
        cancelled_order = {"id": order_id, "status": "cancelled", "user_id": user_id}
        mock_database.fetchrow.return_value = cancelled_order
        mock_database.execute.return_value = None
        
        # Act
        result = await order_service.cancel_order(order_id, user_id)
        
        # Assert
        assert result["status"] == "cancelled"
        mock_database.execute.assert_called_once()
        mock_notification_service.send_push_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_order_unauthorized(self, order_service, mock_database):
        """Test order cancellation by unauthorized user"""
        # Arrange
        order_id = "order_123"
        user_id = "unauthorized_user"
        existing_order = {"id": order_id, "user_id": "different_user", "status": "pending"}
        mock_database.fetchrow.return_value = existing_order
        
        # Act & Assert
        with pytest.raises(Exception, match="Unauthorized"):
            await order_service.cancel_order(order_id, user_id)
    
    @pytest.mark.asyncio
    async def test_calculate_order_total(self, order_service):
        """Test order total calculation"""
        # Arrange
        items = [
            {"quantity": 2, "price": 29.99},
            {"quantity": 1, "price": 15.50},
            {"quantity": 3, "price": 10.00}
        ]
        
        # Act
        total = order_service.calculate_order_total(items)
        
        # Assert
        expected_total = (2 * 29.99) + (1 * 15.50) + (3 * 10.00)
        assert total == expected_total
    
    @pytest.mark.asyncio
    async def test_validate_order_items_valid(self, order_service, mock_database):
        """Test order validation with valid items"""
        # Arrange
        items = [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1}
        ]
        mock_database.fetch.return_value = [
            {"id": 1, "stock": 10, "is_available": True, "price": 29.99},
            {"id": 2, "stock": 5, "is_available": True, "price": 15.50}
        ]
        
        # Act
        result = await order_service.validate_order_items(items)
        
        # Assert
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_order_items_invalid(self, order_service, mock_database):
        """Test order validation with invalid items"""
        # Arrange
        items = [
            {"product_id": 1, "quantity": 15}  # More than stock
        ]
        mock_database.fetch.return_value = [
            {"id": 1, "stock": 10, "is_available": True, "price": 29.99}
        ]
        
        # Act
        result = await order_service.validate_order_items(items)
        
        # Assert
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_order_history_with_pagination(self, order_service, mock_database):
        """Test getting order history with pagination"""
        # Arrange
        user_id = "test_user_123"
        limit = 10
        offset = 0
        orders = [{"id": f"order_{i}", "user_id": user_id} for i in range(5)]
        mock_database.fetch.return_value = orders
        
        # Act
        result = await order_service.get_order_history(user_id, limit, offset)
        
        # Assert
        assert len(result) == 5
        mock_database.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_orders_by_status(self, order_service, mock_database):
        """Test getting orders by status"""
        # Arrange
        status = "pending"
        orders = [{"id": "order_1", "status": status}, {"id": "order_2", "status": status}]
        mock_database.fetch.return_value = orders
        
        # Act
        result = await order_service.get_orders_by_status(status)
        
        # Assert
        assert len(result) == 2
        assert all(order["status"] == status for order in result)
        mock_database.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_delivery_status(self, order_service, mock_database, mock_notification_service):
        """Test updating delivery status"""
        # Arrange
        order_id = "order_123"
        delivery_status = "out_for_delivery"
        updated_order = {"id": order_id, "delivery_status": delivery_status, "user_id": "test_user_123"}
        mock_database.fetchrow.return_value = updated_order
        mock_database.execute.return_value = None
        
        # Act
        result = await order_service.update_delivery_status(order_id, delivery_status)
        
        # Assert
        assert result["delivery_status"] == delivery_status
        mock_database.execute.assert_called_once()
        mock_notification_service.send_push_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_order_id(self, order_service):
        """Test order ID generation"""
        # Act
        order_id = order_service.generate_order_id()
        
        # Assert
        assert order_id is not None
        assert len(order_id) > 10
        assert order_id.startswith("ORD")
    
    @pytest.mark.asyncio
    async def test_process_refund(self, order_service, mock_database):
        """Test processing order refund"""
        # Arrange
        order_id = "order_123"
        refund_amount = 59.98
        mock_database.execute.return_value = None
        
        # Act
        result = await order_service.process_refund(order_id, refund_amount)
        
        # Assert
        assert result is True
        mock_database.execute.assert_called_once()