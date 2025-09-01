from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.audit import AuditLog, AuditEventType, RiskLevel
from fastapi import Request
import json
from typing import Dict, Any, Optional
import re
import html
import logging

logger = logging.getLogger(__name__)

class AuditService:
    """Comprehensive audit logging service"""
    
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'key', 'credential', 
        'authorization', 'cookie', 'session', 'otp', 'pin'
    }
    
    RISK_PATTERNS = {
        RiskLevel.CRITICAL: [
            r'(?i)(drop|delete|truncate)\s+table',
            r'(?i)union\s+select',
            r'(?i)<script[^>]*>.*?</script>',
            r'(?i)javascript:',
        ],
        RiskLevel.HIGH: [
            r'(?i)(select|insert|update|delete)\s+.*\s+(from|into|set)',
            r'(?i)exec\s*\(',
            r'(?i)eval\s*\(',
        ],
        RiskLevel.MEDIUM: [
            r'(?i)(admin|root|administrator)',
            r'(?i)(../|..\\)',
            r'(?i)file://',
        ]
    }
    
    @staticmethod
    def sanitize_data(data: Any) -> Any:
        """Remove sensitive information from data"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in AuditService.SENSITIVE_FIELDS):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = AuditService.sanitize_data(value)
            return sanitized
        elif isinstance(data, list):
            return [AuditService.sanitize_data(item) for item in data]
        elif isinstance(data, str):
            # Redact potential sensitive patterns
            for sensitive in AuditService.SENSITIVE_FIELDS:
                if sensitive in data.lower():
                    return "***REDACTED***"
            return data
        return data
    
    @staticmethod
    def calculate_risk_level(request_data: str, response_data: str, event_type: AuditEventType) -> RiskLevel:
        """Calculate risk level based on request/response content"""
        combined_data = f"{request_data} {response_data}".lower()
        
        # Check for critical patterns
        for pattern in AuditService.RISK_PATTERNS[RiskLevel.CRITICAL]:
            if re.search(pattern, combined_data):
                return RiskLevel.CRITICAL
        
        # Check for high risk patterns
        for pattern in AuditService.RISK_PATTERNS[RiskLevel.HIGH]:
            if re.search(pattern, combined_data):
                return RiskLevel.HIGH
        
        # Check for medium risk patterns
        for pattern in AuditService.RISK_PATTERNS[RiskLevel.MEDIUM]:
            if re.search(pattern, combined_data):
                return RiskLevel.MEDIUM
        
        # Event-based risk assessment
        high_risk_events = {
            AuditEventType.PASSWORD_CHANGE,
            AuditEventType.ADMIN_ACTION,
            AuditEventType.SECURITY_VIOLATION
        }
        
        if event_type in high_risk_events:
            return RiskLevel.HIGH
        
        return RiskLevel.LOW
    
    @staticmethod
    async def log_event(
        db: AsyncSession,
        event_type: AuditEventType,
        request: Request,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ):
        """Log an audit event"""
        try:
            # Sanitize sensitive data
            sanitized_request = AuditService.sanitize_data(request_data) if request_data else None
            sanitized_response = AuditService.sanitize_data(response_data) if response_data else None
            sanitized_details = AuditService.sanitize_data(details) if details else None
            
            # Calculate risk level
            risk_level = AuditService.calculate_risk_level(
                json.dumps(sanitized_request) if sanitized_request else "",
                json.dumps(sanitized_response) if sanitized_response else "",
                event_type
            )
            
            # Create audit log entry
            audit_log = AuditLog(
                event_type=event_type,
                user_id=user_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent") if request.headers else None,
                endpoint=str(request.url.path) if request.url else None,
                method=request.method if hasattr(request, 'method') else None,
                status_code=status_code,
                risk_level=risk_level,
                details=sanitized_details,
                request_data=sanitized_request,
                response_data=sanitized_response
            )
            
            db.add(audit_log)
            await db.commit()
            
            # Alert on high-risk events
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                await AuditService._send_security_alert(audit_log)
                
        except Exception as e:
            # Don't let audit logging break the main application
            logger.error(f"Audit logging failed: {str(e)}")
            try:
                await db.rollback()
            except:
                pass
    
    @staticmethod
    async def _send_security_alert(audit_log: AuditLog):
        """Send alert for high-risk security events"""
        # In production, integrate with alerting system (email, Slack, etc.)
        logger.critical(f"SECURITY ALERT: {audit_log.event_type} - Risk: {audit_log.risk_level}")
        logger.critical(f"User: {audit_log.user_id}, IP: {audit_log.ip_address}")
        logger.critical(f"Endpoint: {audit_log.endpoint}, Time: {audit_log.timestamp}")
    
    @staticmethod
    async def get_security_events(
        db: AsyncSession,
        risk_level: Optional[RiskLevel] = None,
        limit: int = 100
    ):
        """Get recent security events for monitoring"""
        query = select(AuditLog).order_by(AuditLog.timestamp.desc())
        
        if risk_level:
            query = query.where(AuditLog.risk_level == risk_level)
        
        query = query.limit(limit)
        result = await db.execute(query)
        return result.scalars().all()