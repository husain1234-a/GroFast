from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any
from ..config.database import get_db
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

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

@router.post("/fcm")
async def send_fcm_notification(request: FCMNotificationRequest):
    """Send FCM push notification (internal use)"""
    result = await NotificationService.send_fcm_notification(
        request.fcm_tokens, request.title, request.body, request.data
    )
    return {"message": "Notification sent", "result": result}

@router.post("/email")
async def send_email(request: EmailRequest):
    """Send email notification (internal use)"""
    result = await NotificationService.send_email(
        request.to_email, request.subject, request.html_content
    )
    return {"message": "Email sent", "result": result}

@router.post("/sms")
async def send_sms(request: SMSRequest):
    """Send SMS notification (internal use)"""
    result = await NotificationService.send_sms(request.phone, request.message)
    return {"message": "SMS sent", "result": result}