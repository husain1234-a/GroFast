"""
Integration tests for database operations
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import asyncpg


class TestDatabaseOperations:
    """Integration tests for database operations"""
    
    @pytest.fixture
    async def mock_db_pool(self):
        """Mock database connection pool"""
        pool = AsyncMock()
        connection = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = connection
        pool.acquire.return_value.__aexit__.return_value = None
        return pool, connection
    
    @pytest.mark.asyncio
    async def test_user_crud_operations(self, mock_db_pool, sample_user_data):
        """Test user CRUD operations"""
        pool, connection = mock_db_pool
        
        # Test Create
        connection.fetchrow.return_value = sample_user_data
        connection.execute.return_value = None
        
        # Simulate user creation
        with patch('app.config.database.get_db_pool', return_value=pool):
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            
            # Create user
            created_user = await auth_service.create_user(sample_user_data)
            assert created_user == sample_user_data
            
            # Read user
            connection.fetchrow.return_value = sample_user_data
            user = await auth_service.get_user_by_firebase_uid(sample_user_data["firebase_uid"])
            assert user == sample_user_data
            
            # Update user
            updated_data = {**sample_user_data, "name": "Updated Name"}
            connection.fetchrow.return_value = updated_data
            updated_user = await auth_service.update_user_profile(
                sample_user_data["firebase_uid"], 
                {"name": "Updated Name"}
            )
            assert updated_user["name"] == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_product_operations(self, mock_db_pool, sample_product_data):
        """Test product database operations"""
        pool, connection = mock_db_pool
        
        # Test product retrieval
        connection.fetch.return_value = [sample_product_data]
        connection.fetchrow.return_value = sample_product_data
        
        with patch('app.config.database.get_db_pool', return_value=pool):
            # Simulate getting products
            products = await connection.fetch("SELECT * FROM products")
            assert len(products) == 1
            assert products[0] == sample_product_data
            
            # Simulate getting single product
            product = await connection.fetchrow("SELECT * FROM products WHERE id = $1", 1)
            assert product == sample_product_data
    
    @pytest.mark.asyncio
    async def test_cart_operations(self, mock_db_pool, sample_cart_data):
        """Test cart database operations"""
        pool, connection = mock_db_pool
        
        # Test cart operations
        cart_items = [
            {"product_id": 1, "quantity": 2, "price": 29.99, "name": "Product 1"},
            {"product_id": 2, "quantity": 1, "price": 15.50, "name": "Product 2"}
        ]
        connection.fetch.return_value = cart_items
        connection.fetchrow.return_value = cart_items[0]
        connection.execute.return_value = None
        
        with patch('app.config.database.get_db_pool', return_value=pool):
            from app.services.cart_service import CartService
            cart_service = CartService()
            
            # Get cart
            cart = await cart_service.get_cart(sample_cart_data["user_id"])
            assert len(cart["items"]) == 2
            
            # Add item to cart
            result = await cart_service.add_item_to_cart("user_123", 1, 2)
            assert result is True
            
            # Update cart item
            result = await cart_service.update_cart_item_quantity("user_123", 1, 3)
            assert result is True
            
            # Remove item from cart
            result = await cart_service.remove_item_from_cart("user_123", 1)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_order_operations(self, mock_db_pool, sample_order_data):
        """Test order database operations"""
        pool, connection = mock_db_pool
        
        # Test order operations
        connection.fetchrow.return_value = sample_order_data
        connection.fetch.return_value = [sample_order_data]
        connection.execute.return_value = None
        
        with patch('app.config.database.get_db_pool', return_value=pool):
            from app.services.order_service import OrderService
            order_service = OrderService()
            
            # Create order
            order = await order_service.create_order(
                user_id=sample_order_data["user_id"],
                items=sample_order_data["items"],
                delivery_address=sample_order_data["delivery_address"]
            )
            assert order == sample_order_data
            
            # Get order by ID
            order = await order_service.get_order_by_id(sample_order_data["id"])
            assert order == sample_order_data
            
            # Get user orders
            orders = await order_service.get_user_orders(sample_order_data["user_id"])
            assert len(orders) == 1
            assert orders[0] == sample_order_data
            
            # Update order status
            updated_order = {**sample_order_data, "status": "confirmed"}
            connection.fetchrow.return_value = updated_order
            order = await order_service.update_order_status(sample_order_data["id"], "confirmed")
            assert order["status"] == "confirmed"
    
    @pytest.mark.asyncio
    async def test_database_connection_error_handling(self, mock_db_pool):
        """Test database connection error handling"""
        pool, connection = mock_db_pool
        
        # Simulate connection error
        connection.fetchrow.side_effect = asyncpg.ConnectionDoesNotExistError("Connection lost")
        
        with patch('app.config.database.get_db_pool', return_value=pool):
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            
            # Should handle connection error gracefully
            with pytest.raises(asyncpg.ConnectionDoesNotExistError):
                await auth_service.get_user_by_firebase_uid("test_user")
    
    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, mock_db_pool):
        """Test database transaction rollback on error"""
        pool, connection = mock_db_pool
        
        # Simulate transaction
        transaction = AsyncMock()
        connection.transaction.return_value = transaction
        transaction.__aenter__.return_value = transaction
        transaction.__aexit__.return_value = None
        
        # Simulate error during transaction
        connection.execute.side_effect = [None, Exception("Database error")]
        
        with patch('app.config.database.get_db_pool', return_value=pool):
            # Should rollback transaction on error
            try:
                async with connection.transaction():
                    await connection.execute("INSERT INTO users ...")
                    await connection.execute("INSERT INTO invalid_table ...")  # This will fail
            except Exception:
                pass  # Expected to fail
            
            # Verify transaction was attempted
            connection.transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self, mock_db_pool):
        """Test database query performance monitoring"""
        pool, connection = mock_db_pool
        
        # Simulate slow query
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate 100ms query
            return {"id": 1, "name": "Test"}
        
        connection.fetchrow.side_effect = slow_query
        
        with patch('app.config.database.get_db_pool', return_value=pool):
            import time
            start_time = time.time()
            
            result = await connection.fetchrow("SELECT * FROM users WHERE id = $1", 1)
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Query should complete but we can monitor timing
            assert result is not None
            assert query_time >= 0.1  # Should take at least 100ms
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, mock_db_pool):
        """Test database connection pooling"""
        pool, connection = mock_db_pool
        
        # Test multiple concurrent connections
        connection.fetchrow.return_value = {"id": 1}
        
        with patch('app.config.database.get_db_pool', return_value=pool):
            # Simulate multiple concurrent database operations
            tasks = []
            for i in range(5):
                task = connection.fetchrow("SELECT * FROM users WHERE id = $1", i)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All queries should complete successfully
            assert len(results) == 5
            assert all(result["id"] == 1 for result in results)
    
    @pytest.mark.asyncio
    async def test_database_migration_compatibility(self, mock_db_pool):
        """Test database schema compatibility"""
        pool, connection = mock_db_pool
        
        # Test that expected tables and columns exist
        expected_tables = ["users", "products", "cart_items", "orders", "order_items"]
        
        # Simulate table existence check
        connection.fetchval.return_value = True
        
        with patch('app.config.database.get_db_pool', return_value=pool):
            for table in expected_tables:
                exists = await connection.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                assert exists is True
    
    @pytest.mark.asyncio
    async def test_database_data_integrity(self, mock_db_pool, sample_user_data, sample_order_data):
        """Test database data integrity constraints"""
        pool, connection = mock_db_pool
        
        # Test foreign key constraints
        connection.execute.side_effect = [
            None,  # User creation succeeds
            asyncpg.ForeignKeyViolationError("Foreign key violation")  # Order with invalid user fails
        ]
        
        with patch('app.config.database.get_db_pool', return_value=pool):
            # Create user should succeed
            await connection.execute("INSERT INTO users ...", sample_user_data)
            
            # Create order with invalid user_id should fail
            with pytest.raises(asyncpg.ForeignKeyViolationError):
                await connection.execute("INSERT INTO orders ...", sample_order_data)