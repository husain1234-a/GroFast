from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Text, 
    Enum, CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..config.database import Base

class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delivery_partner_id = Column(Integer, ForeignKey("delivery_partners.id"))
    total_amount = Column(Float, CheckConstraint('total_amount > 0'), nullable=False)
    delivery_fee = Column(Float, CheckConstraint('delivery_fee >= 0'), default=0)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    delivery_address = Column(Text, nullable=False)
    delivery_latitude = Column(String(20))
    delivery_longitude = Column(String(20))
    estimated_delivery_time = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_order_user_status', 'user_id', 'status'),
        Index('idx_order_delivery_partner', 'delivery_partner_id'),
        Index('idx_order_created_at', 'created_at'),
    )
    
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    user = relationship("User")
    delivery_partner = relationship("DeliveryPartner")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, CheckConstraint('quantity > 0'), nullable=False)
    price = Column(Float, CheckConstraint('price > 0'), nullable=False)  # Price at time of order
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product")