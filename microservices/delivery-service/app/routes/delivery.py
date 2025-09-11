from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from ..database import get_db
from ..models.delivery import DeliveryPartner, DeliveryLocation, DeliveryStatus
from ..schemas.delivery import (
    DeliveryPartnerResponse, LocationUpdate, DeliveryStatusUpdate, 
    DeliveryLocationResponse
)
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from custom_logging import setup_logging

logger = setup_logging("delivery-service", log_level="INFO")

router = APIRouter()

async def get_delivery_partner_id(x_user_id: str = Header(...)) -> int:
    """Get delivery partner ID from header"""
    try:
        return int(x_user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid delivery partner ID")

@router.get("/me", response_model=DeliveryPartnerResponse)
async def get_delivery_partner_info(
    partner_id: int = Depends(get_delivery_partner_id),
    db: AsyncSession = Depends(get_db)
):
    """Get delivery partner info"""
    logger.info(f"Fetching delivery partner info for ID: {partner_id}")
    result = await db.execute(
        select(DeliveryPartner).where(DeliveryPartner.id == partner_id)
    )
    partner = result.scalar_one_or_none()
    
    if not partner:
        logger.warning(f"Delivery partner not found: {partner_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found")
    
    return DeliveryPartnerResponse.model_validate(partner)

@router.put("/status", response_model=DeliveryPartnerResponse)
async def update_delivery_status(
    status_update: DeliveryStatusUpdate,
    partner_id: int = Depends(get_delivery_partner_id),
    db: AsyncSession = Depends(get_db)
):
    """Update delivery partner status"""
    logger.info(f"Updating delivery partner {partner_id} status to {status_update.status}")
    result = await db.execute(
        select(DeliveryPartner).where(DeliveryPartner.id == partner_id)
    )
    partner = result.scalar_one_or_none()
    
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found")
    
    partner.status = status_update.status
    await db.commit()
    await db.refresh(partner)
    
    # Send notification if status is out_for_delivery
    if status_update.status == DeliveryStatus.BUSY:
        await _send_delivery_notification(partner_id, "out_for_delivery")
    
    logger.info(f"Delivery partner {partner_id} status updated to {status_update.status}")
    return DeliveryPartnerResponse.model_validate(partner)

@router.post("/location", response_model=DeliveryLocationResponse)
async def update_location(
    location: LocationUpdate,
    partner_id: int = Depends(get_delivery_partner_id),
    db: AsyncSession = Depends(get_db)
):
    """Update delivery partner location"""
    logger.info(f"Updating location for delivery partner {partner_id}")
    
    # Update partner's current location
    result = await db.execute(
        select(DeliveryPartner).where(DeliveryPartner.id == partner_id)
    )
    partner = result.scalar_one_or_none()
    
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found")
    
    partner.current_latitude = str(location.latitude)
    partner.current_longitude = str(location.longitude)
    
    # Create location record
    location_record = DeliveryLocation(
        delivery_partner_id=partner_id,
        order_id=location.order_id,
        latitude=location.latitude,
        longitude=location.longitude
    )
    db.add(location_record)
    
    await db.commit()
    await db.refresh(location_record)
    
    # Sync to Supabase for real-time tracking
    await _sync_location_to_supabase(location_record)
    
    # Send location update notification
    if location.order_id:
        await _send_location_notification(partner_id, location.order_id, location.latitude, location.longitude)
    
    logger.info(f"Location updated for delivery partner {partner_id}")
    return DeliveryLocationResponse.model_validate(location_record)

@router.get("/orders")
async def get_assigned_orders(
    partner_id: int = Depends(get_delivery_partner_id),
    db: AsyncSession = Depends(get_db)
):
    """Get orders assigned to delivery partner"""
    logger.info(f"Fetching assigned orders for delivery partner {partner_id}")
    
    # This would typically query the order service
    # For now, return empty list as placeholder
    return {"orders": [], "partner_id": partner_id}

async def _sync_location_to_supabase(location_record: DeliveryLocation):
    """Sync location to Supabase for real-time tracking"""
    try:
        from supabase import create_client
        import os
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if supabase_url and supabase_key:
            supabase = create_client(supabase_url, supabase_key)
            supabase.table('delivery_locations').insert({
                'delivery_partner_id': location_record.delivery_partner_id,
                'order_id': location_record.order_id,
                'latitude': location_record.latitude,
                'longitude': location_record.longitude
            }).execute()
            logger.info(f"Location synced to Supabase for partner {location_record.delivery_partner_id}")
    except Exception as e:
        logger.error(f"Failed to sync location to Supabase: {e}")

async def _send_delivery_notification(partner_id: int, status: str):
    """Send delivery status notification"""
    try:
        from http_client import HTTPClient
        client = HTTPClient()
        
        notification_data = {
            "delivery_partner_id": partner_id,
            "status": status
        }
        
        await client.post(
            "http://notification-service:8000/notifications/delivery-status",
            json=notification_data
        )
        logger.info(f"Delivery notification sent for partner {partner_id}")
    except Exception as e:
        logger.error(f"Failed to send delivery notification: {e}")

@router.get("/internal/stats")
async def get_delivery_stats(db: AsyncSession = Depends(get_db)):
    """Get delivery statistics for admin dashboard"""
    try:
        # Count active delivery partners
        active_result = await db.execute(
            select(func.count(DeliveryPartner.id)).where(DeliveryPartner.status == DeliveryStatus.AVAILABLE)
        )
        active_count = active_result.scalar()
        
        # Count busy delivery partners
        busy_result = await db.execute(
            select(func.count(DeliveryPartner.id)).where(DeliveryPartner.status == DeliveryStatus.BUSY)
        )
        busy_count = busy_result.scalar()
        
        return {
            "active_partners": active_count,
            "busy_partners": busy_count,
            "total_partners": active_count + busy_count
        }
    except Exception as e:
        logger.error(f"Failed to get delivery stats: {e}")
        return {
            "active_partners": 0,
            "busy_partners": 0,
            "total_partners": 0
        }

async def _send_location_notification(partner_id: int, order_id: int, latitude: float, longitude: float):
    """Send location update notification"""
    try:
        from http_client import HTTPClient
        client = HTTPClient()
        
        notification_data = {
            "user_id": 0,
            "order_id": order_id,
            "delivery_partner": f"Partner {partner_id}",
            "location_data": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
        
        await client.post(
            "http://notification-service:8000/notifications/delivery-update",
            json=notification_data
        )
        logger.info(f"Location notification sent for order {order_id}")
    except Exception as e:
        logger.error(f"Failed to send location notification: {e}")