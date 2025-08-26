from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .services.notification_service import NotificationService

app = FastAPI(title="Notification Service", version="1.0.0")
notification_service = NotificationService()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class FCMRequest(BaseModel):
    fcm_tokens: List[str]
    title: str
    body: str
    data: Optional[dict] = None

class OrderNotificationRequest(BaseModel):
    user_id: int
    order_id: int
    status: str

class DeliveryNotificationRequest(BaseModel):
    user_id: int
    partner_name: str
    eta_minutes: int

class InvoiceEmailRequest(BaseModel):
    user_email: str
    order_data: Dict[str, Any]

@app.get("/health")
async def health(): return {"status": "healthy", "service": "Notification Service"}

@app.post("/notifications/fcm")
async def send_fcm_notification(request: FCMRequest):
    return await notification_service.send_fcm_notification(
        request.fcm_tokens, request.title, request.body, request.data
    )

@app.post("/notifications/order")
async def send_order_notification(request: OrderNotificationRequest):
    return await notification_service.send_order_notification(
        request.user_id, request.order_id, request.status
    )

@app.post("/notifications/delivery")
async def send_delivery_notification(request: DeliveryNotificationRequest):
    return await notification_service.send_delivery_notification(
        request.user_id, request.partner_name, request.eta_minutes
    )

@app.post("/notifications/invoice-email")
async def send_invoice_email(request: InvoiceEmailRequest):
    return await notification_service.send_invoice_email(
        request.user_email, request.order_data
    )