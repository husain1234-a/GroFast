import logging
import sys
import os
from typing import Optional, Dict, Any
import json
import uuid
import time
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Enhanced JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": os.getpid(),
            "thread_id": record.thread
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields with safe access
        extra_fields = [
            'user_id', 'request_id', 'service_name', 'correlation_id',
            'method', 'path', 'status_code', 'duration_ms', 'client_ip',
            'user_agent', 'response_size', 'database_query_time',
            'cache_hit', 'external_service_call'
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)
        
        return json.dumps(log_entry, default=str)

def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    enable_json: bool = True,
    log_file: Optional[str] = None,
    enable_file_logging: bool = True
) -> logging.Logger:
    """Setup enhanced structured logging for microservices"""
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    if enable_json:
        json_formatter = JSONFormatter()
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file_logging:
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Set default log file name
        if not log_file:
            log_file = f"logs/{service_name.lower().replace(' ', '_')}.log"
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        if enable_json:
            file_handler.setFormatter(json_formatter)
        else:
            file_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
    
    # Add service name and correlation ID support to all log records
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service_name = service_name
        
        # Try to get correlation ID from context (if available)
        try:
            import contextvars
            correlation_id = getattr(contextvars, 'correlation_id', None)
            if correlation_id:
                record.correlation_id = correlation_id.get()
        except:
            pass
        
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    return logger

# Context variable for correlation ID
try:
    import contextvars
    correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar('correlation_id')
except ImportError:
    correlation_id = None

def set_correlation_id(request_id: str):
    """Set correlation ID for current context"""
    if correlation_id:
        correlation_id.set(request_id)

def get_correlation_id() -> Optional[str]:
    """Get correlation ID from current context"""
    if correlation_id:
        try:
            return correlation_id.get()
        except LookupError:
            return None
    return None

class RequestLoggingMiddleware:
    """Enhanced middleware for logging HTTP requests and responses"""
    
    def __init__(self, app, logger: logging.Logger):
        self.app = app
        self.logger = logger
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Set correlation ID in context
        set_correlation_id(request_id)
        
        # Extract request details
        method = scope["method"]
        path = scope["path"]
        query_string = scope.get("query_string", b"").decode()
        headers = dict(scope.get("headers", []))
        
        # Get client info
        client_ip = None
        user_agent = None
        
        for name, value in headers.items():
            name_str = name.decode() if isinstance(name, bytes) else name
            value_str = value.decode() if isinstance(value, bytes) else value
            
            if name_str.lower() == "x-forwarded-for":
                client_ip = value_str.split(",")[0].strip()
            elif name_str.lower() == "user-agent":
                user_agent = value_str
        
        if not client_ip and scope.get("client"):
            client_ip = scope["client"][0]
        
        # Log request start
        self.logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query_string": query_string,
                "client_ip": client_ip,
                "user_agent": user_agent
            }
        )
        
        # Track response details
        status_code = None
        response_size = 0
        
        # Wrap send to log response and track size
        async def send_wrapper(message):
            nonlocal status_code, response_size
            
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_size += len(body)
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Request failed: {method} {path} - {type(e).__name__}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
        else:
            # Log successful completion
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine log level based on status code
            if status_code and status_code >= 400:
                log_level = "warning" if status_code < 500 else "error"
                log_method = getattr(self.logger, log_level)
            else:
                log_method = self.logger.info
            
            log_method(
                f"Request completed: {method} {path} - {status_code}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "response_size": response_size,
                    "client_ip": client_ip
                }
            )

class HealthCheckLogger:
    """Specialized logger for health check operations"""
    
    def __init__(self, logger: logging.Logger, service_name: str):
        self.logger = logger
        self.service_name = service_name
    
    def log_health_check(self, check_type: str, status: str, details: Dict[str, Any] = None):
        """Log health check results"""
        self.logger.info(
            f"Health check: {check_type} - {status}",
            extra={
                "health_check_type": check_type,
                "health_status": status,
                "service_name": self.service_name,
                **(details or {})
            }
        )
    
    def log_dependency_check(self, dependency: str, status: str, response_time_ms: float = None, error: str = None):
        """Log dependency health check results"""
        extra_data = {
            "dependency_name": dependency,
            "dependency_status": status,
            "service_name": self.service_name
        }
        
        if response_time_ms is not None:
            extra_data["dependency_response_time_ms"] = response_time_ms
        
        if error:
            extra_data["dependency_error"] = error
        
        if status == "healthy":
            self.logger.info(f"Dependency check: {dependency} - {status}", extra=extra_data)
        else:
            self.logger.warning(f"Dependency check: {dependency} - {status}", extra=extra_data)