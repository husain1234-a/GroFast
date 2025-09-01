from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.delivery import DeliveryPartner, DeliveryLocation, DeliveryStatus
from supabase import create_client, Client
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from http_client import ResilientHttpClient
from circuit_breaker import CircuitBreaker, RetryConfig

class DeliveryService:
    # Initialize resilient HTTP client for order service
    _order_client = None
    
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    @classmethod
    def get_order_client(cls) -> ResilientHttpClient:
        if cls._order_client is None:
            cls._order_client = ResilientHttpClient(
                base_url="http://localhost:8004",
                timeout=5.0,
                circuit_breaker=CircuitBreaker(name="OrderService"),
                retry_config=RetryConfig(max_attempts=3, base_delay=0.5)
            )
        return cls._order_client
    
    @staticmethod
    async def get_delivery_partner(db: AsyncSession, firebase_uid: str):
        result = await db.execute(
            select(DeliveryPartner).where(DeliveryPartner.firebase_uid == firebase_uid)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_status(db: AsyncSession, firebase_uid: str, status: DeliveryStatus):
        result = await db.execute(
            select(DeliveryPartner).where(DeliveryPartner.firebase_uid == firebase_uid)
        )
        partner = result.scalar_one_or_none()
        
        if partner:
            partner.status = status
            await db.commit()
            await db.refresh(partner)
        
        return partner
    
    async def update_location(self, db: AsyncSession, firebase_uid: str, latitude: float, longitude: float, order_id: int = None):
        # Update in PostgreSQL
        result = await db.execute(
            select(DeliveryPartner).where(DeliveryPartner.firebase_uid == firebase_uid)
        )
        partner = result.scalar_one_or_none()
        
        if partner:
            partner.current_latitude = str(latitude)
            partner.current_longitude = str(longitude)
            
            # Save location history
            location = DeliveryLocation(
                delivery_partner_id=partner.id,
                order_id=order_id,
                latitude=latitude,
                longitude=longitude
            )
            db.add(location)
            await db.commit()
            
            # Update Supabase for real-time tracking
            try:
                self.supabase.table('delivery_locations').insert({
                    'delivery_partner_id': partner.id,
                    'order_id': order_id,
                    'latitude': latitude,
                    'longitude': longitude
                }).execute()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Supabase update failed: {e}")
                try:
                    await db.rollback()
                except:
                    pass
        
        return partner
    
    @staticmethod
    async def get_assigned_orders(db: AsyncSession, firebase_uid: str):
        partner = await DeliveryService.get_delivery_partner(db, firebase_uid)
        if not partner:
            return []
        
        # Get orders from Order Service using resilient client
        order_client = DeliveryService.get_order_client()
        try:
            response = await order_client.get(f"/orders/assigned/{partner.id}")
            if response.status_code == 200:
                return response.json()
            else:
                # Order service error - return empty list as fallback
                return []
        except Exception as e:
            # Circuit breaker or network error - return empty list as fallback
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get assigned orders from Order Service: {e}")
            return []