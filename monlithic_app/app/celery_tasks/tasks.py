from . import celery_app
from ..services.notification_service import NotificationService
from ..supabase.client import supabase_client
from typing import Dict, Any, List

@celery_app.task
def send_order_notification(fcm_tokens: List[str], order_id: int, status: str):
    """Send order status notification"""
    title = "Order Update"
    body = f"Your order #{order_id} is now {status.replace('_', ' ').title()}"
    data = {"order_id": str(order_id), "status": status}
    
    return NotificationService.send_fcm_notification(fcm_tokens, title, body, data)

@celery_app.task
def send_delivery_notification(fcm_tokens: List[str], message: str, data: Dict[str, Any] = None):
    """Send delivery partner notification"""
    title = "Delivery Update"
    
    return NotificationService.send_fcm_notification(fcm_tokens, title, message, data or {})

@celery_app.task
def sync_location_to_supabase(delivery_partner_id: int, order_id: int, latitude: float, longitude: float):
    """Sync delivery location to Supabase for real-time tracking"""
    location_data = {
        "delivery_partner_id": delivery_partner_id,
        "order_id": order_id,
        "latitude": latitude,
        "longitude": longitude
    }
    
    return supabase_client.insert_delivery_location(location_data)

@celery_app.task
def send_order_confirmation_email(email: str, order_id: int, total_amount: float):
    """Send order confirmation email"""
    subject = f"Order Confirmation - #{order_id}"
    html_content = f"""
    <h2>Order Confirmed!</h2>
    <p>Your order #{order_id} has been confirmed.</p>
    <p>Total Amount: ₹{total_amount}</p>
    <p>Estimated delivery: 30 minutes</p>
    <p>Thank you for choosing Blinkit Clone!</p>
    """
    
    return NotificationService.send_email(email, subject, html_content)

@celery_app.task
def send_delivery_assignment_sms(phone: str, order_id: int):
    """Send SMS to delivery partner for new assignment"""
    message = f"New delivery assigned! Order #{order_id}. Please check the app for details."
    
    return NotificationService.send_sms(phone, message)