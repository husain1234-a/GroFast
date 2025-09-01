from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..services.notification_service import NotificationService
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from custom_logging import setup_logging

logger = setup_logging("notification-service", log_level="INFO")

router = APIRouter()

class FCMNotificationRequest(BaseModel):
    fcm_tokens: List[str]
    title: str
    body: str
    data: Dict[str, Any] = {}

class EmailRequest(BaseModel):
    to_email: str
    subject: str
    html_content: str

class SMSRequest(BaseModel):
    phone: str
    message: str

class OrderNotificationRequest(BaseModel):
    user_id: int
    order_id: int
    status: str
    fcm_token: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    total_amount: Optional[float] = None

@router.post("/fcm")
async def send_fcm_notification(request: FCMNotificationRequest):
    """Send FCM push notification"""
    logger.info(f"Sending FCM notification to {len(request.fcm_tokens)} tokens")
    service = NotificationService()
    
    results = []
    for token in request.fcm_tokens:
        try:
            success = await service.send_fcm_notification(
                token, 
                {"title": request.title, "body": request.body}, 
                request.data
            )
            results.append({"token": token, "success": success})
            logger.info(f"FCM notification sent to token: {token[:10]}...")
        except Exception as e:
            results.append({"token": token, "success": False, "error": str(e)})
            logger.error(f"Failed to send FCM notification to {token[:10]}...: {e}")
    
    return {"message": "FCM notifications processed", "results": results}

@router.post("/email")
async def send_email(request: EmailRequest):
    """Send email notification"""
    logger.info(f"Sending email to: {request.to_email}")
    service = NotificationService()
    
    try:
        success = await service.send_email_notification(
            request.to_email,
            request.subject,
            request.html_content
        )
        logger.info(f"Email sent successfully to: {request.to_email}")
        return {"message": "Email sent", "success": success}
    except Exception as e:
        logger.error(f"Failed to send email to {request.to_email}: {e}")
        return {"message": "Email failed", "success": False, "error": str(e)}

@router.post("/sms")
async def send_sms(request: SMSRequest):
    """Send SMS notification"""
    logger.info(f"Sending SMS to: {request.phone}")
    service = NotificationService()
    
    try:
        success = await service.send_sms_notification(
            request.phone,
            request.message
        )
        logger.info(f"SMS sent successfully to: {request.phone}")
        return {"message": "SMS sent", "success": success}
    except Exception as e:
        logger.error(f"Failed to send SMS to {request.phone}: {e}")
        return {"message": "SMS failed", "success": False, "error": str(e)}

@router.post("/order-status")
async def send_order_notification(request: OrderNotificationRequest):
    """Send order status notification"""
    logger.info(f"Sending order notification for order {request.order_id} to user {request.user_id}")
    service = NotificationService()
    
    results = {}
    
    # Send FCM notification
    if request.fcm_token:
        try:
            fcm_success = await service.send_fcm_notification(
                request.fcm_token,
                {
                    "title": f"Order {request.status.title()}",
                    "body": f"Your order #{request.order_id} is {request.status}"
                },
                {"order_id": request.order_id, "status": request.status}
            )
            results["fcm"] = fcm_success
        except Exception as e:
            results["fcm"] = False
            logger.error(f"FCM notification failed: {e}")
    
    # Send email notification
    if request.email:
        try:
            email_success = await service.send_email_notification(
                request.email,
                f"Order Update - #{request.order_id}",
                f"<h2>Order Update</h2><p>Your order #{request.order_id} is {request.status}</p>"
            )
            results["email"] = email_success
        except Exception as e:
            results["email"] = False
            logger.error(f"Email notification failed: {e}")
    
    logger.info(f"Order notification sent for order {request.order_id}")
    return {"message": "Order notification sent", "results": results}