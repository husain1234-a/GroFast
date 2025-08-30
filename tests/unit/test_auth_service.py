"""
Unit tests for Authentication Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.auth_service import AuthService
from app.models.user import User


class TestAuthService:
    """Test cases for AuthService"""
    
    @pytest.fixture
    def auth_service(self, mock_database, mock_redis, mock_firebase_auth):
        """Create AuthService instance with mocked dependencies"""
        service = AuthService()
        service.db = mock_database
        service.redis = mock_redis
        service.firebase_auth = mock_firebase_auth
        return service
    
    @pytest.mark.asyncio
    async def test_verify_firebase_token_success(self, auth_service, mock_firebase_auth):
        """Test successful Firebase token verification"""
        # Arrange
        token = "valid_firebase_token"
        expected_user_data = {
            "uid": "test_user_123",
            "email": "test@example.com",
            "name": "Test User"
        }
        mock_firebase_auth.verify_id_token.return_value = expected_user_data
        
        # Act
        result = await auth_service.verify_firebase_token(token)
        
        # Assert
        assert result == expected_user_data
        mock_firebase_auth.verify_id_token.assert_called_once_with(token)
    
    @pytest.mark.asyncio
    async def test_verify_firebase_token_invalid(self, auth_service, mock_firebase_auth):
        """Test Firebase token verification with invalid token"""
        # Arrange
        token = "invalid_firebase_token"
        mock_firebase_auth.verify_id_token.side_effect = Exception("Invalid token")
        
        # Act & Assert
        with pytest.raises(Exception, match="Invalid token"):
            await auth_service.verify_firebase_token(token)
    
    @pytest.mark.asyncio
    async def test_create_user_session_success(self, auth_service, mock_redis, sample_user_data):
        """Test successful user session creation"""
        # Arrange
        user_id = sample_user_data["firebase_uid"]
        session_data = {"user_id": user_id, "created_at": "2023-01-01T00:00:00"}
        mock_redis.set.return_value = True
        
        # Act
        session_id = await auth_service.create_user_session(user_id, session_data)
        
        # Assert
        assert session_id is not None
        assert len(session_id) > 10  # Should be a proper session ID
        mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_session_valid(self, auth_service, mock_redis):
        """Test session validation with valid session"""
        # Arrange
        session_id = "valid_session_123"
        session_data = '{"user_id": "test_user_123", "created_at": "2023-01-01T00:00:00"}'
        mock_redis.get.return_value = session_data
        
        # Act
        result = await auth_service.validate_session(session_id)
        
        # Assert
        assert result is not None
        assert result["user_id"] == "test_user_123"
        mock_redis.get.assert_called_once_with(f"session:{session_id}")
    
    @pytest.mark.asyncio
    async def test_validate_session_invalid(self, auth_service, mock_redis):
        """Test session validation with invalid session"""
        # Arrange
        session_id = "invalid_session_123"
        mock_redis.get.return_value = None
        
        # Act
        result = await auth_service.validate_session(session_id)
        
        # Assert
        assert result is None
        mock_redis.get.assert_called_once_with(f"session:{session_id}")
    
    @pytest.mark.asyncio
    async def test_invalidate_session(self, auth_service, mock_redis):
        """Test session invalidation"""
        # Arrange
        session_id = "session_to_invalidate"
        mock_redis.delete.return_value = 1
        
        # Act
        result = await auth_service.invalidate_session(session_id)
        
        # Assert
        assert result is True
        mock_redis.delete.assert_called_once_with(f"session:{session_id}")
    
    @pytest.mark.asyncio
    async def test_get_user_by_firebase_uid(self, auth_service, mock_database, sample_user_data):
        """Test getting user by Firebase UID"""
        # Arrange
        firebase_uid = sample_user_data["firebase_uid"]
        mock_database.fetchrow.return_value = sample_user_data
        
        # Act
        result = await auth_service.get_user_by_firebase_uid(firebase_uid)
        
        # Assert
        assert result == sample_user_data
        mock_database.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user(self, auth_service, mock_database, sample_user_data):
        """Test user creation"""
        # Arrange
        mock_database.fetchrow.return_value = sample_user_data
        
        # Act
        result = await auth_service.create_user(sample_user_data)
        
        # Assert
        assert result == sample_user_data
        mock_database.execute.assert_called_once()
        mock_database.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_profile(self, auth_service, mock_database, sample_user_data):
        """Test user profile update"""
        # Arrange
        user_id = sample_user_data["firebase_uid"]
        update_data = {"name": "Updated Name", "address": "New Address"}
        updated_user = {**sample_user_data, **update_data}
        mock_database.fetchrow.return_value = updated_user
        
        # Act
        result = await auth_service.update_user_profile(user_id, update_data)
        
        # Assert
        assert result["name"] == "Updated Name"
        assert result["address"] == "New Address"
        mock_database.execute.assert_called_once()
        mock_database.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_session(self, auth_service, mock_redis):
        """Test session refresh"""
        # Arrange
        session_id = "session_to_refresh"
        session_data = '{"user_id": "test_user_123", "created_at": "2023-01-01T00:00:00"}'
        mock_redis.get.return_value = session_data
        mock_redis.set.return_value = True
        
        # Act
        result = await auth_service.refresh_session(session_id)
        
        # Assert
        assert result is True
        mock_redis.get.assert_called_once()
        mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, auth_service, mock_redis):
        """Test getting all user sessions"""
        # Arrange
        user_id = "test_user_123"
        mock_redis.keys.return_value = [f"session:session1", f"session:session2"]
        mock_redis.get.side_effect = [
            '{"user_id": "test_user_123", "created_at": "2023-01-01T00:00:00"}',
            '{"user_id": "test_user_123", "created_at": "2023-01-01T01:00:00"}'
        ]
        
        # Act
        result = await auth_service.get_user_sessions(user_id)
        
        # Assert
        assert len(result) == 2
        assert all(session["user_id"] == user_id for session in result)
    
    @pytest.mark.asyncio
    async def test_invalidate_all_user_sessions(self, auth_service, mock_redis):
        """Test invalidating all user sessions"""
        # Arrange
        user_id = "test_user_123"
        mock_redis.keys.return_value = [f"session:session1", f"session:session2"]
        mock_redis.delete.return_value = 2
        
        # Act
        result = await auth_service.invalidate_all_user_sessions(user_id)
        
        # Assert
        assert result == 2
        mock_redis.keys.assert_called_once()
        mock_redis.delete.assert_called_once()