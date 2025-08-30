import json
import os
import sys
from typing import List, Dict, Any
from datetime import datetime

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from http_client import ResilientHttpClient
from circuit_breaker import CircuitBreaker, RetryConfig

class NotificationService:
    # Initialize resilient HTTP clients for external services
    _fcm_client = None
    _resend_client = None
    
    def __init__(self):
        self.fcm_server_key = os.getenv('FCM_SERVER_KEY', 'demo-key')
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.resend_api_key = os.getenv('RESEND_API_KEY', '')
        self.resend_url = "https://api.resend.com/emails"
    
    @classmethod
    def get_fcm_client(cls) -> ResilientHttpClient:
        if cls._fcm_client is None:
            cls._fcm_client = ResilientHttpClient(
                base_url="https://fcm.googleapis.com",
                timeout=10.0,
                circuit_breaker=CircuitBreaker(name="FCMService"),
                retry_config=RetryConfig(max_attempts=2, base_delay=1.0)
            )
        return cls._fcm_client
    
    @classmethod
    def get_resend_client(cls) -> ResilientHttpClient:
        if cls._resend_client is None:
            cls._resend_client = ResilientHttpClient(
                base_url="https://api.resend.com",
                timeout=15.0,
                circuit_breaker=CircuitBreaker(name="ResendService"),
                retry_config=RetryConfig(max_attempts=2, base_delay=1.0)
            )
        return cls._resend_client
    
    async def send_fcm_notification(self, fcm_tokens: List[str], title: str, body: str, data: dict = None):
        if not self.fcm_server_key or not fcm_tokens:
            return {"success": False, "message": "Missing FCM configuration or tokens"}
        
        headers = {
            "Authorization": f"key={self.fcm_server_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "registration_ids": fcm_tokens,
            "notification": {
                "title": title,
                "body": body
            },
            "data": data or {}
        }
        
        try:
            fcm_client = self.get_fcm_client()
            response = await fcm_client.post(
                "/fcm/send",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": "Notification sent successfully",
                    "results": result
                }
            else:
                return {
                    "success": False,
                    "message": f"FCM request failed: {response.status_code}",
                    "error": response.text
                }
        except Exception as e:
            # Circuit breaker or network error - use fallback
            if "Circuit breaker" in str(e):
                return {
                    "success": False,
                    "message": "FCM service temporarily unavailable",
                    "fallback": True
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to send notification: {str(e)}"
                }
    
    async def send_order_notification(self, user_id: int, order_id: int, status: str):
        # Mock implementation for demo
        return {
            "success": True,
            "message": f"Order notification sent to user {user_id} for order {order_id} with status {status}"
        }
    
    async def send_delivery_notification(self, user_id: int, partner_name: str, eta_minutes: int):
        # Mock implementation for demo
        return {
            "success": True,
            "message": f"Delivery notification sent to user {user_id} for partner {partner_name} with ETA {eta_minutes} minutes"
        }
    
    async def send_invoice_email(self, user_email: str, order_data: Dict[str, Any]):
        """Send invoice email via Resend when order is delivered"""
        if not self.resend_api_key or not user_email:
            return {"success": False, "message": "Missing Resend API key or user email"}
        
        # Generate invoice HTML
        invoice_html = self._generate_invoice_html(order_data)
        
        headers = {
            "Authorization": f"Bearer {self.resend_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": "GroFast <orders@grofast.com>",
            "to": [user_email],
            "subject": f"Invoice for Order #{order_data.get('id', 'N/A')} - GroFast",
            "html": invoice_html
        }
        
        try:
            resend_client = self.get_resend_client()
            response = await resend_client.post(
                "/emails",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": "Invoice email sent successfully",
                    "email_id": result.get('id')
                }
            else:
                return {
                    "success": False,
                    "message": f"Resend API failed: {response.status_code}",
                    "error": response.text
                }
        except Exception as e:
            # Circuit breaker or network error - use fallback
            if "Circuit breaker" in str(e):
                return {
                    "success": False,
                    "message": "Email service temporarily unavailable",
                    "fallback": True
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to send invoice email: {str(e)}"
                }
    
    def _generate_invoice_html(self, order_data: Dict[str, Any]) -> str:
        """Generate HTML invoice template"""
        items_html = ""
        total_amount = 0
        
        for item in order_data.get('items', []):
            item_total = item.get('price', 0) * item.get('quantity', 0)
            total_amount += item_total
            items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{item.get('product_name', 'Unknown')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{item.get('quantity', 0)}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">₹{item.get('price', 0):.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">₹{item_total:.2f}</td>
            </tr>
            """
        
        delivery_fee = order_data.get('delivery_fee', 0)
        grand_total = total_amount + delivery_fee
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Invoice - GroFast</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2c5530; margin: 0;">GroFast</h1>
                    <p style="color: #666; margin: 5px 0 0 0;">Ultra-fast grocery delivery</p>
                </div>
                
                <div style="border-bottom: 2px solid #2c5530; padding-bottom: 20px; margin-bottom: 20px;">
                    <h2 style="color: #2c5530; margin: 0;">Invoice</h2>
                    <p style="margin: 5px 0;">Order ID: #{order_data.get('id', 'N/A')}</p>
                    <p style="margin: 5px 0;">Date: {datetime.now().strftime('%B %d, %Y')}</p>
                    <p style="margin: 5px 0;">Status: Delivered ✅</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #333; margin-bottom: 10px;">Delivery Address:</h3>
                    <p style="margin: 0; color: #666;">{order_data.get('delivery_address', 'N/A')}</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 12px 8px; text-align: left; border-bottom: 2px solid #dee2e6;">Item</th>
                            <th style="padding: 12px 8px; text-align: center; border-bottom: 2px solid #dee2e6;">Qty</th>
                            <th style="padding: 12px 8px; text-align: right; border-bottom: 2px solid #dee2e6;">Price</th>
                            <th style="padding: 12px 8px; text-align: right; border-bottom: 2px solid #dee2e6;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
                
                <div style="border-top: 2px solid #dee2e6; padding-top: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>Subtotal:</span>
                        <span>₹{total_amount:.2f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>Delivery Fee:</span>
                        <span>₹{delivery_fee:.2f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 18px; color: #2c5530; border-top: 1px solid #dee2e6; padding-top: 8px;">
                        <span>Total:</span>
                        <span>₹{grand_total:.2f}</span>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #666;">
                    <p>Thank you for choosing GroFast!</p>
                    <p style="font-size: 12px;">For support, contact us at support@grofast.com</p>
                </div>
            </div>
        </body>
        </html>
        """