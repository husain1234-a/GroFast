from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
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