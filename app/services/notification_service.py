import httpx
from ..config.settings import settings
from typing import Dict, Any, List

class NotificationService:
    @staticmethod
    async def send_fcm_notification(fcm_tokens: List[str], title: str, body: str, data: Dict[str, Any] = None):
        """Send FCM push notification"""
        if not fcm_tokens:
            return
        
        headers = {
            'Authorization': f'key={settings.fcm_server_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'registration_ids': fcm_tokens,
            'notification': {
                'title': title,
                'body': body
            },
            'data': data or {}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    'https://fcm.googleapis.com/fcm/send',
                    json=payload,
                    headers=headers
                )
                return response.json()
            except Exception as e:
                print(f"FCM Error: {e}")
                return None
    
    @staticmethod
    async def send_email(to_email: str, subject: str, html_content: str):
        """Send email via Resend"""
        headers = {
            'Authorization': f'Bearer {settings.resend_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'from': 'noreply@blinkit-clone.com',
            'to': [to_email],
            'subject': subject,
            'html': html_content
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    'https://api.resend.com/emails',
                    json=payload,
                    headers=headers
                )
                return response.json()
            except Exception as e:
                print(f"Email Error: {e}")
                return None
    
    @staticmethod
    async def send_sms(phone: str, message: str):
        """Send SMS via Textbelt"""
        payload = {
            'phone': phone,
            'message': message,
            'key': settings.textbelt_api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    'https://textbelt.com/text',
                    data=payload
                )
                return response.json()
            except Exception as e:
                print(f"SMS Error: {e}")
                return None