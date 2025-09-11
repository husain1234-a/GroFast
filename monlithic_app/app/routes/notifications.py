from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..config.database import get_db
from ..services.notification_service import (
    NotificationService, 
    NotificationType, 
    NotificationChannel,
    notify_order_status_change,
    notify_delivery_update
)
from ..services.auth_service import AuthService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class SendNotificationRequest(BaseModel):
    user_id: int
    notification_type: NotificationType
    channels: List[NotificationChannel]
    data: Dict[str, Any] = {}
    fcm_token: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class OrderNotificationRequest(BaseModel):
    user_id: int
    order_id: int
    status: str
    fcm_token: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    total_amount: Optional[float] = None
    estimated_delivery: Optional[str] = None
    delivery_partner: Optional[str] = None

class DeliveryUpdateRequest(BaseModel):
    user_id: int
    order_id: int
    delivery_partner: str
    latitude: float
    longitude: float
    distance: Optional[str] = None
    eta: Optional[str] = None
    fcm_token: Optional[str] = None
    phone: Optional[str] = None

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

class TestNotificationRequest(BaseModel):
    fcm_token: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

# Main notification endpoints
@router.post("/send")
async def send_notification(request: SendNotificationRequest):
    """Send notification across multiple channels"""
    service = NotificationService()
    
    result = await service.send_notification(
        user_id=request.user_id,
        notification_type=request.notification_type,
        channels=request.channels,
        data=request.data,
        fcm_token=request.fcm_token,
        email=request.email,
        phone=request.phone
    )
    
    return {"message": "Notification sent", "results": result}

@router.post("/order-status")
async def send_order_notification(request: OrderNotificationRequest):
    """Send order status notification"""
    result = await notify_order_status_change(
        user_id=request.user_id,
        order_id=request.order_id,
        status=request.status,
        fcm_token=request.fcm_token,
        email=request.email,
        phone=request.phone,
        total_amount=request.total_amount,
        estimated_delivery=request.estimated_delivery,
        delivery_partner=request.delivery_partner
    )
    
    return {"message": "Order notification sent", "results": result}

@router.post("/delivery-update")
async def send_delivery_update(request: DeliveryUpdateRequest):
    """Send delivery location update notification"""
    location_data = {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "distance": request.distance,
        "eta": request.eta
    }
    
    result = await notify_delivery_update(
        user_id=request.user_id,
        order_id=request.order_id,
        delivery_partner=request.delivery_partner,
        location_data=location_data,
        fcm_token=request.fcm_token,
        phone=request.phone
    )
    
    return {"message": "Delivery update sent", "results": result}

# Test endpoints
@router.post("/test")
async def test_notifications(
    request: TestNotificationRequest,
    firebase_token: str = Query(..., description="Firebase token for authentication")
):
    """Test notification system with sample data"""
    # Get user info for testing
    from ..config.database import get_db
    
    # Mock user data for testing
    test_user_id = 1
    test_order_id = 12345
    
    service = NotificationService()
    
    # Determine available channels
    channels = [NotificationChannel.IN_APP]
    if request.fcm_token:
        channels.append(NotificationChannel.FCM)
    if request.email:
        channels.append(NotificationChannel.EMAIL)
    if request.phone:
        channels.append(NotificationChannel.SMS)
    
    # Send test notification
    result = await service.send_notification(
        user_id=test_user_id,
        notification_type=NotificationType.ORDER_CREATED,
        channels=channels,
        data={
            "order_id": test_order_id,
            "total_amount": 299.99,
            "estimated_delivery": "30-40 minutes",
            "notification_type": "order_created"
        },
        fcm_token=request.fcm_token,
        email=request.email,
        phone=request.phone
    )
    
    return {
        "message": "Test notifications sent",
        "channels_tested": [ch.value for ch in channels],
        "results": result
    }

# Legacy endpoints for backward compatibility
@router.post("/fcm")
async def send_fcm_notification(request: FCMNotificationRequest):
    """Send FCM push notification (legacy endpoint)"""
    service = NotificationService()
    
    results = []
    for token in request.fcm_tokens:
        try:
            success = await service._send_fcm_notification(
                token, 
                {"title": request.title, "body": request.body}, 
                request.data
            )
            results.append({"token": token, "success": success})
        except Exception as e:
            results.append({"token": token, "success": False, "error": str(e)})
    
    return {"message": "FCM notifications processed", "results": results}

@router.post("/email")
async def send_email(request: EmailRequest):
    """Send email notification (legacy endpoint)"""
    service = NotificationService()
    
    # Convert to new format
    content = {
        "title": request.subject,
        "body": request.html_content,
        "email_subject": request.subject
    }
    
    success = await service._send_email_notification(
        request.to_email, 
        content, 
        {"notification_type": "custom"}
    )
    
    return {"message": "Email processed", "success": success}

@router.post("/sms")
async def send_sms(request: SMSRequest):
    """Send SMS notification (legacy endpoint)"""
    service = NotificationService()
    
    content = {"sms_text": request.message}
    
    success = await service._send_sms_notification(
        request.phone, 
        content, 
        {"notification_type": "custom"}
    )
    
    return {"message": "SMS processed", "success": success}

# Notification preferences endpoints
@router.get("/preferences/{user_id}")
async def get_notification_preferences(
    user_id: int,
    firebase_token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get user notification preferences"""
    # Verify user access
    user = await AuthService.create_or_get_user(db, firebase_token)
    if user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement notification preferences storage
    # For now, return default preferences
    return {
        "user_id": user_id,
        "preferences": {
            "order_updates": {
                "fcm": True,
                "email": True,
                "sms": True
            },
            "delivery_updates": {
                "fcm": True,
                "email": False,
                "sms": True
            },
            "promotional": {
                "fcm": True,
                "email": False,
                "sms": False
            }
        }
    }

@router.put("/preferences/{user_id}")
async def update_notification_preferences(
    user_id: int,
    preferences: Dict[str, Any],
    firebase_token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Update user notification preferences"""
    # Verify user access
    user = await AuthService.create_or_get_user(db, firebase_token)
    if user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Store preferences in database
    # For now, just return success
    return {
        "message": "Notification preferences updated",
        "user_id": user_id,
        "preferences": preferences
    }