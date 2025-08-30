"""
Unit tests for Notification Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.notification_service import NotificationService


class TestNotificationService:
    """Test cases for NotificationService"""
    
    @pytest.fixture
    def notification_service(self, mock_database):
        """Create NotificationService instance with mocked dependencies"""
        service = NotificationService()
        service.db = mock_database
        return service
    
    @pytest.mark.asyncio
    @patch('firebase_admin.messaging.send')
    async def test_send_push_notification_success(self, mock_firebase_send, notification_service):
        """Test successful push notification sending"""
        # Arrange
        fcm_token = "test_fcm_token"
        title = "Test Notification"
        body = "This is a test notification"
        mock_firebase_send.return_value = "message_id_123"
        
        # Act
        result = await notification_service.send_push_notification(fcm_token, title, body)
        
        # Assert
        assert result is True
        mock_firebase_send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('firebase_admin.messaging.send')
    async def test_send_push_notification_failure(self, mock_firebase_send, notification_service):
        """Test push notification sending failure"""
        # Arrange
        fcm_token = "invalid_fcm_token"
        title = "Test Notification"
        body = "This is a test notification"
        mock_firebase_send.side_effect = Exception("Invalid token")
        
        # Act
        result = await notification_service.send_push_notification(fcm_token, title, body)
        
        # Assert
        assert result is False
        mock_firebase_send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.send')
    async def test_send_email_notification_success(self, mock_smtp_send, notification_service):
        """Test successful email notification sending"""
        # Arrange
        email = "test@example.com"
        subject = "Test Email"
        body = "This is a test email"
        mock_smtp_send.return_value = None
        
        # Act
        result = await notification_service.send_email_notification(email, subject, body)
        
        # Assert
        assert result is True
        mock_smtp_send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.send')
    async def test_send_email_notification_failure(self, mock_smtp_send, notification_service):
        """Test email notification sending failure"""
        # Arrange
        email = "invalid@example.com"
        subject = "Test Email"
        body = "This is a test email"
        mock_smtp_send.side_effect = Exception("SMTP error")
        
        # Act
        result = await notification_service.send_email_notification(email, subject, body)
        
        # Assert
        assert result is False
        mock_smtp_send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('twilio.rest.Client')
    async def test_send_sms_notification_success(self, mock_twilio_client, notification_service):
        """Test successful SMS notification sending"""
        # Arrange
        phone = "+1234567890"
        message = "This is a test SMS"
        mock_client_instance = Mock()
        mock_twilio_client.return_value = mock_client_instance
        mock_client_instance.messages.create.return_value = Mock(sid="SMS123")
        
        # Act
        result = await notification_service.send_sms_notification(phone, message)
        
        # Assert
        assert result is True
        mock_client_instance.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('twilio.rest.Client')
    async def test_send_sms_notification_failure(self, mock_twilio_client, notification_service):
        """Test SMS notification sending failure"""
        # Arrange
        phone = "+invalid"
        message = "This is a test SMS"
        mock_client_instance = Mock()
        mock_twilio_client.return_value = mock_client_instance
        mock_client_instance.messages.create.side_effect = Exception("Invalid phone number")
        
        # Act
        result = await notification_service.send_sms_notification(phone, message)
        
        # Assert
        assert result is False
        mock_client_instance.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_order_status_change(self, notification_service, mock_database):
        """Test order status change notification"""
        # Arrange
        order_id = "order_123"
        user_id = "test_user_123"
        new_status = "confirmed"
        user_data = {
            "fcm_token": "test_fcm_token",
            "email": "test@example.com",
            "phone": "+1234567890"
        }
        mock_database.fetchrow.return_value = user_data
        
        with patch.object(notification_service, 'send_push_notification', return_value=True) as mock_push, \
             patch.object(notification_service, 'send_email_notification', return_value=True) as mock_email:
            
            # Act
            result = await notification_service.notify_order_status_change(order_id, user_id, new_status)
            
            # Assert
            assert result is True
            mock_push.assert_called_once()
            mock_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_order_confirmation(self, notification_service, mock_database):
        """Test order confirmation notification"""
        # Arrange
        order_data = {
            "id": "order_123",
            "user_id": "test_user_123",
            "total": 59.98,
            "items": [{"name": "Product 1", "quantity": 2}]
        }
        user_data = {
            "fcm_token": "test_fcm_token",
            "email": "test@example.com"
        }
        mock_database.fetchrow.return_value = user_data
        
        with patch.object(notification_service, 'send_push_notification', return_value=True) as mock_push, \
             patch.object(notification_service, 'send_email_notification', return_value=True) as mock_email:
            
            # Act
            result = await notification_service.send_order_confirmation(order_data)
            
            # Assert
            assert result is True
            mock_push.assert_called_once()
            mock_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_delivery_update(self, notification_service, mock_database):
        """Test delivery update notification"""
        # Arrange
        order_id = "order_123"
        user_id = "test_user_123"
        delivery_status = "out_for_delivery"
        estimated_time = "30 minutes"
        user_data = {
            "fcm_token": "test_fcm_token",
            "phone": "+1234567890"
        }
        mock_database.fetchrow.return_value = user_data
        
        with patch.object(notification_service, 'send_push_notification', return_value=True) as mock_push, \
             patch.object(notification_service, 'send_sms_notification', return_value=True) as mock_sms:
            
            # Act
            result = await notification_service.send_delivery_update(order_id, user_id, delivery_status, estimated_time)
            
            # Assert
            assert result is True
            mock_push.assert_called_once()
            mock_sms.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_promotional_notification(self, notification_service, mock_database):
        """Test promotional notification sending"""
        # Arrange
        user_ids = ["user_1", "user_2", "user_3"]
        title = "Special Offer"
        message = "Get 20% off on your next order!"
        mock_database.fetch.return_value = [
            {"user_id": "user_1", "fcm_token": "token_1"},
            {"user_id": "user_2", "fcm_token": "token_2"},
            {"user_id": "user_3", "fcm_token": "token_3"}
        ]
        
        with patch.object(notification_service, 'send_push_notification', return_value=True) as mock_push:
            
            # Act
            result = await notification_service.send_promotional_notification(user_ids, title, message)
            
            # Assert
            assert result is True
            assert mock_push.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_notification_preferences(self, notification_service, mock_database):
        """Test getting user notification preferences"""
        # Arrange
        user_id = "test_user_123"
        preferences = {
            "push_notifications": True,
            "email_notifications": True,
            "sms_notifications": False
        }
        mock_database.fetchrow.return_value = preferences
        
        # Act
        result = await notification_service.get_notification_preferences(user_id)
        
        # Assert
        assert result == preferences
        mock_database.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_notification_preferences(self, notification_service, mock_database):
        """Test updating user notification preferences"""
        # Arrange
        user_id = "test_user_123"
        new_preferences = {
            "push_notifications": False,
            "email_notifications": True,
            "sms_notifications": True
        }
        mock_database.execute.return_value = None
        
        # Act
        result = await notification_service.update_notification_preferences(user_id, new_preferences)
        
        # Assert
        assert result is True
        mock_database.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_notification_sent(self, notification_service, mock_database):
        """Test logging sent notifications"""
        # Arrange
        user_id = "test_user_123"
        notification_type = "order_confirmation"
        channel = "push"
        success = True
        mock_database.execute.return_value = None
        
        # Act
        result = await notification_service.log_notification_sent(user_id, notification_type, channel, success)
        
        # Assert
        assert result is True
        mock_database.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_notification_history(self, notification_service, mock_database):
        """Test getting notification history"""
        # Arrange
        user_id = "test_user_123"
        limit = 10
        notifications = [
            {"id": 1, "type": "order_confirmation", "sent_at": "2023-01-01T00:00:00"},
            {"id": 2, "type": "delivery_update", "sent_at": "2023-01-01T01:00:00"}
        ]
        mock_database.fetch.return_value = notifications
        
        # Act
        result = await notification_service.get_notification_history(user_id, limit)
        
        # Assert
        assert len(result) == 2
        mock_database.fetch.assert_called_once()