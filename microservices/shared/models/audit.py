from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditLog(Base):
    """Audit log model for tracking system events"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, index=True)
    resource_type = Column(String(100), index=True)
    resource_id = Column(String(100), index=True)
    action = Column(String(100), nullable=False)
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog(service={self.service_name}, action={self.action}, timestamp={self.timestamp})>"