from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum, Boolean
from sqlalchemy.sql import func
import enum
from ..database import Base

class DeliveryStatus(enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"
    id = Column(Integer, primary_key=True)
    firebase_uid = Column(String(128), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.OFFLINE)
    current_latitude = Column(String(20))
    current_longitude = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DeliveryLocation(Base):
    __tablename__ = "delivery_locations"
    id = Column(Integer, primary_key=True)
    delivery_partner_id = Column(Integer, ForeignKey("delivery_partners.id"))
    order_id = Column(Integer)
    latitude = Column(Numeric(10,8), nullable=False)
    longitude = Column(Numeric(11,8), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())