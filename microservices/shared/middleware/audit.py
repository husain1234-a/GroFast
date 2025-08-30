from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json
import time
from ..services.audit_service import AuditService
from ..models.audit import AuditEventType

class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for audit purposes"""
    
    def __init__(self, app, db_session_factory):
        super().__init__(app)
        self.db_session_factory = db_session_factory
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Capture request data
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = json.loads(body.decode())
            except:
                request_body = {"error": "Could not parse request body"}
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log the event
        try:
            async with self.db_session_factory() as db:
                await AuditService.log_event(
                    db=db,
                    event_type=AuditEventType.API_ACCESS,
                    request=request,
                    user_id=getattr(request.state, 'user_id', None),
                    details={
                        "processing_time": process_time,
                        "query_params": dict(request.query_params)
                    },
                    request_data=request_body,
                    status_code=response.status_code
                )
        except Exception as e:
            # Don't break the request if audit logging fails
            print(f"Audit logging failed: {str(e)}")
        
        return response