from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.audit import AuditLog
from fastapi import Request
import json
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditService:
    """Persistent audit logging service"""
    

    
    @staticmethod
    async def record_event(
        service_name: str,
        event_type: str,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Record audit event to database"""
        try:
            from ..database import get_db
            
            async with get_db() as db:
                audit_log = AuditLog(
                    service_name=service_name,
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                db.add(audit_log)
                await db.commit()
                
                logger.info(f"Audit event recorded: {service_name}.{event_type}.{action}")
                
        except Exception as e:
            logger.error(f"Failed to record audit event: {e}")
    
    @staticmethod
    async def get_audit_logs(
        service_name: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ):
        """Get audit logs with filtering"""
        try:
            from ..database import get_db
            
            async with get_db() as db:
                query = select(AuditLog).order_by(AuditLog.timestamp.desc())
                
                if service_name:
                    query = query.where(AuditLog.service_name == service_name)
                
                if event_type:
                    query = query.where(AuditLog.event_type == event_type)
                
                query = query.limit(limit)
                result = await db.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []