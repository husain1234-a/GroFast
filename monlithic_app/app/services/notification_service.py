"""
Comprehensive Notification Service
Handles FCM push notifications and email notifications via Resend API
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

import firebase_admin
from firebase_admin import messaging
import aiohttp
from jinja2 import Template

from ..config.settings import settings

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    ORDER_CREATED = "order_created"
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_PREPARING = "order_preparing"
    ORDER_OUT_FOR_DELIVERY = "order_out_for_delivery"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"
    DELIVERY_PARTNER_ASSIGNED = "delivery_partner_assigned"
    DELIVERY_LOCATION_UPDATE = "delivery_location_update"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    PROMOTIONAL = "promotional"

class NotificationChannel(str, Enum):
    FCM = "fcm"
    EMAIL = "email"
    IN_APP = "in_app"

class NotificationService:
    """Comprehensive notification service for all communication channels"""
    
    def __init__(self):
        self.fcm_enabled = True
        self.email_enabled = True
        
        # Initialize Firebase for FCM
        try:
            if not firebase_admin._apps:
                # Initialize if not already done
                pass
        except Exception as e:
            logger.error(f"Firebase initialization error: {e}")
            self.fcm_enabled = False
        
        # Check Resend API configuration
        if not settings.resend_api_key:
            logger.warning("Email notifications disabled - Resend API key not configured")
            self.email_enabled = False
    
    async def send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        channels: List[NotificationChannel],
        data: Dict[str, Any],
        fcm_token: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Send notification across multiple channels
        
        Args:
            user_id: User ID for tracking
            notification_type: Type of notification
            channels: List of channels to send notification
            data: Notification data and context
            fcm_token: FCM token for push notifications
            email: Email address for email notifications
            
        Returns:
            Dict with success status for each channel
        """
        results = {}
        
        # Prepare notification content
        content = self._prepare_notification_content(notification_type, data)
        
        # Send to each requested channel
        tasks = []
        
        if NotificationChannel.FCM in channels and fcm_token and self.fcm_enabled:
            tasks.append(self._send_fcm_notification(fcm_token, content, data))
        
        if NotificationChannel.EMAIL in channels and email and self.email_enabled:
            tasks.append(self._send_email_notification(email, content, data))
        
        if NotificationChannel.IN_APP in channels:
            tasks.append(self._send_in_app_notification(user_id, content, data))
        
        # Execute all notifications concurrently
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            active_channels = [ch for ch in channels if (
                (ch == NotificationChannel.FCM and fcm_token and self.fcm_enabled) or
                (ch == NotificationChannel.EMAIL and email and self.email_enabled) or
                (ch == NotificationChannel.IN_APP)
            )]
            
            for i, channel in enumerate(active_channels):
                if i < len(task_results):
                    results[channel.value] = not isinstance(task_results[i], Exception)
                    if isinstance(task_results[i], Exception):
                        logger.error(f"Notification failed for {channel.value}: {task_results[i]}")
        
        # Log notification attempt
        logger.info(f"Notification sent - User: {user_id}, Type: {notification_type.value}, Results: {results}")
        
        return results
    
    def _prepare_notification_content(self, notification_type: NotificationType, data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare notification content based on type and data"""
        
        templates = {
            NotificationType.ORDER_CREATED: {
                "title": "Order Confirmed! 🎉",
                "body": "Your order #{order_id} has been confirmed and is being prepared.",
                "email_subject": "Order Confirmation - #{order_id}"
            },
            NotificationType.ORDER_PREPARING: {
                "title": "Order Being Prepared 👨‍🍳",
                "body": "Your order #{order_id} is being prepared by our team.",
                "email_subject": "Order Update - Being Prepared"
            },
            NotificationType.ORDER_OUT_FOR_DELIVERY: {
                "title": "Out for Delivery 🚚",
                "body": "Your order #{order_id} is out for delivery! Delivery partner: {delivery_partner}",
                "email_subject": "Order Out for Delivery - #{order_id}"
            },
            NotificationType.ORDER_DELIVERED: {
                "title": "Order Delivered! ✅",
                "body": "Your order #{order_id} has been delivered successfully. Enjoy your items!",
                "email_subject": "Order Delivered - #{order_id}"
            },
            NotificationType.ORDER_CANCELLED: {
                "title": "Order Cancelled ❌",
                "body": "Your order #{order_id} has been cancelled. Refund will be processed within 3-5 business days.",
                "email_subject": "Order Cancellation - #{order_id}"
            },
            NotificationType.DELIVERY_LOCATION_UPDATE: {
                "title": "Delivery Update 📍",
                "body": "Your delivery partner is {distance} away from your location.",
                "email_subject": "Delivery Location Update"
            }
        }
        
        template = templates.get(notification_type, {
            "title": "Blinkit Update",
            "body": "You have a new update from Blinkit",
            "email_subject": "Blinkit Notification"
        })
        
        # Format templates with data
        formatted_content = {}
        for key, value in template.items():
            try:
                formatted_content[key] = Template(value).render(**data)
            except Exception as e:
                logger.warning(f"Template formatting error for {key}: {e}")
                formatted_content[key] = value
        
        return formatted_content
    
    async def _send_fcm_notification(self, fcm_token: str, content: Dict[str, str], data: Dict[str, Any]) -> bool:
        """Send FCM push notification"""
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=content["title"],
                    body=content["body"]
                ),
                data={
                    "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    "type": data.get("notification_type", "general"),
                    "order_id": str(data.get("order_id", "")),
                    "timestamp": str(datetime.now().isoformat())
                },
                token=fcm_token,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon="ic_notification",
                        color="#FF6B35",
                        sound="default"
                    ),
                    priority="high"
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=content["title"],
                                body=content["body"]
                            ),
                            badge=1,
                            sound="default"
                        )
                    )
                )
            )
            
            response = messaging.send(message)
            logger.info(f"FCM notification sent successfully: {response}")
            return True
            
        except Exception as e:
            logger.error(f"FCM notification failed: {e}")
            return False
    
    async def _send_email_notification(self, email: str, content: Dict[str, str], data: Dict[str, Any]) -> bool:
        """Send email notification using Resend"""
        try:
            # Create HTML email template
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }
                    .header { background-color: #FF6B35; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                    .content { padding: 20px; }
                    .footer { background-color: #f8f9fa; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; }
                    .button { background-color: #FF6B35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🛒 Blinkit</h1>
                    </div>
                    <div class="content">
                        <h2>{{ title }}</h2>
                        <p>{{ body }}</p>
                        {% if order_id %}
                        <p><strong>Order ID:</strong> #{{ order_id }}</p>
                        {% endif %}
                        {% if total_amount %}
                        <p><strong>Total Amount:</strong> ₹{{ total_amount }}</p>
                        {% endif %}
                        <a href="{{ app_link | default('https://blinkit.com/app') }}" class="button">Open Blinkit App</a>
                    </div>
                    <div class="footer">
                        <p>Thank you for choosing Blinkit!</p>
                        <p>For support, contact us at support@blinkit.com</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_content = Template(html_template).render(
                title=content["title"],
                body=content["body"],
                **data
            )
            
            # Use Resend API exclusively
            if settings.resend_api_key:
                url = "https://api.resend.com/emails"
                headers = {
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "from": "Blinkit <noreply@blinkit.com>",
                    "to": [email],
                    "subject": content["email_subject"],
                    "html": html_content
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Email notification sent successfully to {email} via Resend. ID: {result.get('id')}")
                            return True
                        else:
                            error_text = await response.text()
                            logger.error(f"Resend API error: {response.status} - {error_text}")
                            return False
            else:
                # Log when API key is missing
                logger.warning(f"Resend API key not configured. Email to {email} not sent.")
                return False
            
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False
    

    async def _send_in_app_notification(self, user_id: int, content: Dict[str, str], data: Dict[str, Any]) -> bool:
        """Send in-app notification (store in database for app to fetch)"""
        try:
            # This would typically store in database for the app to fetch
            # For now, we'll log it as a placeholder
            notification_data = {
                "user_id": user_id,
                "title": content["title"],
                "body": content["body"],
                "data": data,
                "created_at": datetime.now().isoformat(),
                "read": False
            }
            
            logger.info(f"In-app notification created: {notification_data}")
            # TODO: Store in database table for in-app notifications
            return True
            
        except Exception as e:
            logger.error(f"In-app notification failed: {e}")
            return False

# Convenience functions for common notification scenarios
async def notify_order_status_change(
    user_id: int,
    order_id: int,
    status: str,
    fcm_token: Optional[str] = None,
    email: Optional[str] = None,
    **kwargs
):
    """Notify user about order status change"""
    service = NotificationService()
    
    # Map status to notification type
    status_mapping = {
        "confirmed": NotificationType.ORDER_CONFIRMED,
        "preparing": NotificationType.ORDER_PREPARING,
        "out_for_delivery": NotificationType.ORDER_OUT_FOR_DELIVERY,
        "delivered": NotificationType.ORDER_DELIVERED,
        "cancelled": NotificationType.ORDER_CANCELLED
    }
    
    notification_type = status_mapping.get(status, NotificationType.ORDER_CREATED)
    
    # Determine channels based on available contact info
    channels = [NotificationChannel.IN_APP]
    if fcm_token:
        channels.append(NotificationChannel.FCM)
    if email:
        channels.append(NotificationChannel.EMAIL)
    
    data = {
        "order_id": order_id,
        "notification_type": notification_type.value,
        **kwargs
    }
    
    return await service.send_notification(
        user_id=user_id,
        notification_type=notification_type,
        channels=channels,
        data=data,
        fcm_token=fcm_token,
        email=email
    )

async def notify_delivery_update(
    user_id: int,
    order_id: int,
    delivery_partner: str,
    location_data: Dict[str, Any],
    fcm_token: Optional[str] = None
):
    """Notify user about delivery location update"""
    service = NotificationService()
    
    channels = [NotificationChannel.IN_APP]
    if fcm_token:
        channels.append(NotificationChannel.FCM)
    
    data = {
        "order_id": order_id,
        "delivery_partner": delivery_partner,
        "notification_type": NotificationType.DELIVERY_LOCATION_UPDATE.value,
        **location_data
    }
    
    return await service.send_notification(
        user_id=user_id,
        notification_type=NotificationType.DELIVERY_LOCATION_UPDATE,
        channels=channels,
        data=data,
        fcm_token=fcm_token
    )