from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.delivery import DeliveryStatus

class DeliveryPartnerBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None

class DeliveryPartnerCreate(DeliveryPartnerBase):
    firebase_uid: str
    fcm_token: Optional[str] = None

class DeliveryPartnerResponse(DeliveryPartnerBase):
    id: int
    firebase_uid: str
    status: DeliveryStatus
    current_latitude: Optional[str] = None
    current_longitude: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    order_id: Optional[int] = None

class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus

class DeliveryLocationResponse(BaseModel):
    id: int
    delivery_partner_id: int
    order_id: Optional[int] = None
    latitude: float
    longitude: float
    timestamp: datetime
    
    class Config:
        from_attributes = True