"""
Unit tests for Cart Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.cart_service import CartService
from app.models.cart import Cart


class TestCartService:
    """Test cases for CartService"""
    
    @pytest.fixture
    def cart_service(self, mock_database, mock_redis):
        """Create CartService instance with mocked dependencies"""
        service = CartService()
        service.db = mock_database
        service.redis = mock_redis
        return service
    
    @pytest.mark.asyncio
    async def test_get_cart_success(self, cart_service, mock_database, sample_cart_data):
        """Test successful cart retrieval"""
        # Arrange
        user_id = sample_cart_data["user_id"]
        mock_database.fetch.return_value = [
            {"product_id": 1, "quantity": 2, "price": 29.99, "name": "Product 1"},
            {"product_id": 2, "quantity": 1, "price": 15.50, "name": "Product 2"}
        ]
        
        # Act
        result = await cart_service.get_cart(user_id)
        
        # Assert
        assert result is not None
        assert len(result["items"]) == 2
        assert result["total"] > 0
        mock_database.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cart_empty(self, cart_service, mock_database):
        """Test cart retrieval for empty cart"""
        # Arrange
        user_id = "test_user_123"
        mock_database.fetch.return_value = []
        
        # Act
        result = await cart_service.get_cart(user_id)
        
        # Assert
        assert result["items"] == []
        assert result["total"] == 0
        mock_database.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_item_to_cart_new_item(self, cart_service, mock_database):
        """Test adding new item to cart"""
        # Arrange
        user_id = "test_user_123"
        product_id = 1
        quantity = 2
        mock_database.fetchrow.return_value = None  # Item doesn't exist
        mock_database.execute.return_value = None
        
        # Act
        result = await cart_service.add_item_to_cart(user_id, product_id, quantity)
        
        # Assert
        assert result is True
        assert mock_database.execute.call_count == 1  # INSERT
    
    @pytest.mark.asyncio
    async def test_add_item_to_cart_existing_item(self, cart_service, mock_database):
        """Test adding quantity to existing cart item"""
        # Arrange
        user_id = "test_user_123"
        product_id = 1
        quantity = 2
        existing_item = {"user_id": user_id, "product_id": product_id, "quantity": 1}
        mock_database.fetchrow.return_value = existing_item
        mock_database.execute.return_value = None
        
        # Act
        result = await cart_service.add_item_to_cart(user_id, product_id, quantity)
        
        # Assert
        assert result is True
        assert mock_database.execute.call_count == 1  # UPDATE
    
    @pytest.mark.asyncio
    async def test_update_cart_item_quantity(self, cart_service, mock_database):
        """Test updating cart item quantity"""
        # Arrange
        user_id = "test_user_123"
        product_id = 1
        new_quantity = 5
        mock_database.execute.return_value = None
        
        # Act
        result = await cart_service.update_cart_item_quantity(user_id, product_id, new_quantity)
        
        # Assert
        assert result is True
        mock_database.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_item_from_cart(self, cart_service, mock_database):
        """Test removing item from cart"""
        # Arrange
        user_id = "test_user_123"
        product_id = 1
        mock_database.execute.return_value = None
        
        # Act
        result = await cart_service.remove_item_from_cart(user_id, product_id)
        
        # Assert
        assert result is True
        mock_database.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_cart(self, cart_service, mock_database):
        """Test clearing entire cart"""
        # Arrange
        user_id = "test_user_123"
        mock_database.execute.return_value = None
        
        # Act
        result = await cart_service.clear_cart(user_id)
        
        # Assert
        assert result is True
        mock_database.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_cart_total(self, cart_service):
        """Test cart total calculation"""
        # Arrange
        cart_items = [
            {"quantity": 2, "price": 29.99},
            {"quantity": 1, "price": 15.50},
            {"quantity": 3, "price": 10.00}
        ]
        
        # Act
        total = cart_service.calculate_cart_total(cart_items)
        
        # Assert
        expected_total = (2 * 29.99) + (1 * 15.50) + (3 * 10.00)
        assert total == expected_total
    
    @pytest.mark.asyncio
    async def test_validate_cart_items_valid(self, cart_service, mock_database):
        """Test cart validation with valid items"""
        # Arrange
        cart_items = [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1}
        ]
        mock_database.fetch.return_value = [
            {"id": 1, "stock": 10, "is_available": True},
            {"id": 2, "stock": 5, "is_available": True}
        ]
        
        # Act
        result = await cart_service.validate_cart_items(cart_items)
        
        # Assert
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_cart_items_insufficient_stock(self, cart_service, mock_database):
        """Test cart validation with insufficient stock"""
        # Arrange
        cart_items = [
            {"product_id": 1, "quantity": 15}  # More than available stock
        ]
        mock_database.fetch.return_value = [
            {"id": 1, "stock": 10, "is_available": True}
        ]
        
        # Act
        result = await cart_service.validate_cart_items(cart_items)
        
        # Assert
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "insufficient stock" in result["errors"][0].lower()
    
    @pytest.mark.asyncio
    async def test_validate_cart_items_unavailable_product(self, cart_service, mock_database):
        """Test cart validation with unavailable product"""
        # Arrange
        cart_items = [
            {"product_id": 1, "quantity": 2}
        ]
        mock_database.fetch.return_value = [
            {"id": 1, "stock": 10, "is_available": False}
        ]
        
        # Act
        result = await cart_service.validate_cart_items(cart_items)
        
        # Assert
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "not available" in result["errors"][0].lower()
    
    @pytest.mark.asyncio
    async def test_get_cart_item_count(self, cart_service, mock_database):
        """Test getting total item count in cart"""
        # Arrange
        user_id = "test_user_123"
        mock_database.fetchval.return_value = 5
        
        # Act
        result = await cart_service.get_cart_item_count(user_id)
        
        # Assert
        assert result == 5
        mock_database.fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_merge_carts(self, cart_service, mock_database):
        """Test merging guest cart with user cart"""
        # Arrange
        user_id = "test_user_123"
        guest_cart_items = [
            {"product_id": 1, "quantity": 2},
            {"product_id": 3, "quantity": 1}
        ]
        mock_database.execute.return_value = None
        
        # Act
        result = await cart_service.merge_carts(user_id, guest_cart_items)
        
        # Assert
        assert result is True
        # Should call execute for each item to merge
        assert mock_database.execute.call_count >= len(guest_cart_items)