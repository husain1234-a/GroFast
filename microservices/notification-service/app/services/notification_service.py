import asyncio
import sys
import os
from typing import Dict, Any

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from custom_circuit_breaker import CircuitBreaker, RetryConfig, CircuitBreakerError

class NotificationService:
    def __init__(self):
        self.fcm_circuit_breaker = CircuitBreaker(name="FCM")
        self.email_circuit_breaker = CircuitBreaker(name="Email")
        self.sms_circuit_breaker = CircuitBreaker(name="SMS")
    
    async def send_fcm_notification(self, token: str, message: Dict[str, str], data: Dict[str, Any]) -> bool:
        """Send FCM notification with circuit breaker"""
        if self.fcm_circuit_breaker.is_open:
            raise CircuitBreakerError("FCM circuit breaker is open")
        
        try:
            # Mock FCM notification
            print(f"FCM: {message['title']} - {message['body']} to {token[:10]}...")
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            self.fcm_circuit_breaker.is_open = True
            raise
    
    async def send_email_notification(self, email: str, subject: str, content: str) -> bool:
        """Send email notification with circuit breaker"""
        if self.email_circuit_breaker.is_open:
            raise CircuitBreakerError("Email circuit breaker is open")
        
        try:
            # Mock email notification
            print(f"Email to {email}: {subject}")
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            self.email_circuit_breaker.is_open = True
            raise
    
    async def send_sms_notification(self, phone: str, message: str) -> bool:
        """Send SMS notification with circuit breaker"""
        if self.sms_circuit_breaker.is_open:
            raise CircuitBreakerError("SMS circuit breaker is open")
        
        try:
            # Mock SMS notification
            print(f"SMS to {phone}: {message}")
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            self.sms_circuit_breaker.is_open = True
            raise