from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class AuditEventType(enum.Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    PASSWORD_CHANGE = "password_change"
    CART_ADD = "cart_add"
    CART_REMOVE = "cart_remove"
    ORDER_CREATE = "order_create"
    ORDER_UPDATE = "order_update"
    PAYMENT_PROCESS = "payment_process"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    SECURITY_VIOLATION = "security_violation"
    API_ACCESS = "api_access"
    ADMIN_ACTION = "admin_action"

class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(AuditEventType), nullable=False, index=True)
    user_id = Column(Integer, index=True)
    session_id = Column(String(255))
    ip_address = Column(String(45), index=True)  # IPv6 compatible
    user_agent = Column(Text)
    endpoint = Column(String(255), index=True)
    method = Column(String(10))
    status_code = Column(Integer)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW, index=True)
    details = Column(JSON)
    request_data = Column(JSON)  # Sanitized request data
    response_data = Column(JSON)  # Sanitized response data
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id})>"