import asyncio
import sys
import os
from typing import Dict, Any
import logging

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from custom_circuit_breaker import CircuitBreaker, RetryConfig, CircuitBreakerError

# Firebase Admin SDK (modern approach)
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    from ..config import settings
    
    # Initialize Firebase Admin SDK
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred)
    
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK not available - using mock notifications")

class NotificationService:
    def __init__(self):
        self.fcm_circuit_breaker = CircuitBreaker(name="FCM")
        self.email_circuit_breaker = CircuitBreaker(name="Email")
        self.sms_circuit_breaker = CircuitBreaker(name="SMS")
    
    async def send_fcm_notification(self, token: str, message: Dict[str, str], data: Dict[str, Any]) -> bool:
        """Send FCM notification using Firebase Admin SDK"""
        if self.fcm_circuit_breaker.is_open:
            raise CircuitBreakerError("FCM circuit breaker is open")
        
        try:
            if FIREBASE_AVAILABLE:
                # Modern Firebase Admin SDK approach
                fcm_message = messaging.Message(
                    notification=messaging.Notification(
                        title=message.get('title', ''),
                        body=message.get('body', '')
                    ),
                    data={str(k): str(v) for k, v in data.items()},  # Convert all to strings
                    token=token
                )
                
                # Send message
                response = messaging.send(fcm_message)
                print(f"FCM sent successfully: {response}")
                return True
            else:
                # Use HTTP API as fallback
                import httpx
                fcm_url = "https://fcm.googleapis.com/fcm/send"
                headers = {
                    "Authorization": f"key={settings.fcm_server_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "to": token,
                    "notification": {
                        "title": message.get('title', ''),
                        "body": message.get('body', '')
                    },
                    "data": {str(k): str(v) for k, v in data.items()}
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(fcm_url, headers=headers, json=payload)
                    if response.status_code == 200:
                        print(f"FCM sent via HTTP API: {token[:10]}...")
                        return True
                    else:
                        print(f"FCM HTTP API error: {response.status_code}")
                        return False
                
        except Exception as e:
            print(f"FCM Error: {e}")
            self.fcm_circuit_breaker.is_open = True
            raise
    
    async def send_email_notification(self, email: str, subject: str, content: str) -> bool:
        """Send email notification with circuit breaker"""
        if self.email_circuit_breaker.is_open:
            raise CircuitBreakerError("Email circuit breaker is open")
        
        try:
            # Use Resend API
            import httpx
            if hasattr(settings, 'resend_api_key') and settings.resend_api_key:
                url = "https://api.resend.com/emails"
                headers = {
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "from": "Blinkit <noreply@blinkit.com>",
                    "to": [email],
                    "subject": subject,
                    "html": content
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        print(f"Email sent to {email}: {subject}")
                        return True
                    else:
                        print(f"Resend API error: {response.status_code}")
                        return False
            else:
                # Mock email notification
                print(f"Email (Mock) to {email}: {subject}")
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