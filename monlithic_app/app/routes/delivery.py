from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..config.database import get_db
from ..models.delivery import DeliveryPartner, DeliveryLocation, DeliveryStatus
from ..models.order import Order, OrderStatus
from ..schemas.delivery import (
    DeliveryPartnerResponse, LocationUpdate, DeliveryStatusUpdate, 
    DeliveryLocationResponse
)
from ..services.auth_service import AuthService
from ..celery_tasks.tasks import sync_location_to_supabase, send_delivery_assignment_sms

router = APIRouter(prefix="/delivery", tags=["Delivery"])

async def get_delivery_partner(firebase_token: str, db: AsyncSession = Depends(get_db)) -> DeliveryPartner:
    """Get delivery partner from Firebase token"""
    from ..firebase.auth import verify_firebase_token
    user_info = await verify_firebase_token(firebase_token)
    
    result = await db.execute(
        select(DeliveryPartner).where(DeliveryPartner.firebase_uid == user_info['uid'])
    )
    partner = result.scalar_one_or_none()
    
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found")
    
    return partner

@router.get("/me", response_model=DeliveryPartnerResponse)
async def get_delivery_partner_info(
    partner: DeliveryPartner = Depends(get_delivery_partner)
):
    """Get delivery partner info"""
    return DeliveryPartnerResponse.model_validate(partner)

@router.put("/status", response_model=DeliveryPartnerResponse)
async def update_delivery_status(
    status_update: DeliveryStatusUpdate,
    partner: DeliveryPartner = Depends(get_delivery_partner),
    db: AsyncSession = Depends(get_db)
):
    """Update delivery partner status"""
    partner.status = status_update.status
    await db.commit()
    await db.refresh(partner)
    return DeliveryPartnerResponse.model_validate(partner)

@router.post("/location", response_model=DeliveryLocationResponse)
async def update_location(
    location: LocationUpdate,
    partner: DeliveryPartner = Depends(get_delivery_partner),
    db: AsyncSession = Depends(get_db)
):
    """Update delivery partner location"""
    # Update partner's current location
    partner.current_latitude = str(location.latitude)
    partner.current_longitude = str(location.longitude)
    
    # Create location record
    location_record = DeliveryLocation(
        delivery_partner_id=partner.id,
        order_id=location.order_id,
        latitude=location.latitude,
        longitude=location.longitude
    )
    db.add(location_record)
    
    await db.commit()
    await db.refresh(location_record)
    
    # Sync to Supabase for real-time tracking
    if location.order_id:
        sync_location_to_supabase.delay(
            partner.id, location.order_id, 
            location.latitude, location.longitude
        )
    
    return DeliveryLocationResponse.model_validate(location_record)

@router.post("/assign/{order_id}")
async def assign_order(
    order_id: int,
    partner_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Assign order to delivery partner (admin only)"""
    # Update order
    await db.execute(
        update(Order).where(Order.id == order_id).values(
            delivery_partner_id=partner_id,
            status=OrderStatus.PREPARING
        )
    )
    
    # Get partner info for SMS
    result = await db.execute(select(DeliveryPartner).where(DeliveryPartner.id == partner_id))
    partner = result.scalar_one_or_none()
    
    if partner:
        # Send SMS notification
        send_delivery_assignment_sms.delay(partner.phone, order_id)
        
        # Update partner status to busy
        partner.status = DeliveryStatus.BUSY
    
    await db.commit()
    
    return {"message": "Order assigned successfully"}

@router.get("/orders")
async def get_assigned_orders(
    partner: DeliveryPartner = Depends(get_delivery_partner),
    db: AsyncSession = Depends(get_db)
):
    """Get orders assigned to delivery partner"""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Order).options(
            selectinload(Order.items).selectinload(Order.items.product)
        ).where(
            Order.delivery_partner_id == partner.id,
            Order.status.in_([OrderStatus.PREPARING, OrderStatus.OUT_FOR_DELIVERY])
        ).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    
    from ..schemas.order import OrderResponse
    return [OrderResponse.model_validate(order) for order in orders]