from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class DeliveryStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    order_id: Optional[int] = None

class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus

class DeliveryPartnerResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    status: DeliveryStatus
    current_latitude: Optional[str] = None
    current_longitude: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class DeliveryLocationResponse(BaseModel):
    id: int
    delivery_partner_id: int
    order_id: Optional[int] = None
    latitude: float
    longitude: float
    timestamp: datetime

    class Config:
        from_attributes = True