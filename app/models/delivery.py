from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..config.database import Base

class DeliveryStatus(enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"
    
    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    email = Column(String(255))
    fcm_token = Column(String(500))
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.OFFLINE)
    current_latitude = Column(String(20))
    current_longitude = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DeliveryLocation(Base):
    __tablename__ = "delivery_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    delivery_partner_id = Column(Integer, ForeignKey("delivery_partners.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    delivery_partner = relationship("DeliveryPartner")
    order = relationship("Order")