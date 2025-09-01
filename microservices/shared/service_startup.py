"""
Service startup utilities with enhanced error handling
Provides standardized initialization patterns for microservices
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List
from contextlib import asynccontextmanager
from service_clients import service_client_manager
from startup_validation import validate_service_startup, StartupValidationError
from custom_logging import setup_logging

logger = logging.getLogger(__name__)

class ServiceInitializationError(Exception):
    """Raised when service initialization fails"""
    pass

class ServiceStartupManager:
    """Manages the complete startup process for a microservice"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = setup_logging(service_name)
        self.initialization_steps: List[Callable] = []
        self.cleanup_steps: List[Callable] = []
        self.health_checks: List[Callable] = []
        
    def add_initialization_step(self, step_func: Callable, step_name: str = None):
        """Add an initialization step to be executed during startup"""
        step_name = step_name or step_func.__name__
        
        async def wrapped_step():
            try:
                self.logger.info(f"Executing initialization step: {step_name}")
                if asyncio.iscoroutinefunction(step_func):
                    await step_func()
                else:
                    step_func()
                self.logger.info(f"Completed initialization step: {step_name}")
            except Exception as e:
                self.logger.error(f"Initialization step '{step_name}' failed: {e}")
                raise ServiceInitializationError(f"Failed to initialize {step_name}: {e}")
        
        self.initialization_steps.append(wrapped_step)
    
    def add_cleanup_step(self, cleanup_func: Callable, step_name: str = None):
        """Add a cleanup step to be executed during shutdown"""
        step_name = step_name or cleanup_func.__name__
        
        async def wrapped_cleanup():
            try:
                self.logger.info(f"Executing cleanup step: {step_name}")
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
                self.logger.info(f"Completed cleanup step: {step_name}")
            except Exception as e:
                self.logger.error(f"Cleanup step '{step_name}' failed: {e}")
                # Don't raise during cleanup, just log
        
        self.cleanup_steps.append(wrapped_cleanup)
    
    def add_health_check(self, health_func: Callable, check_name: str = None):
        """Add a health check function"""
        check_name = check_name or health_func.__name__
        
        async def wrapped_health_check():
            try:
                if asyncio.iscoroutinefunction(health_func):
                    result = await health_func()
                else:
                    result = health_func()
                
                return {
                    "check": check_name,
                    "status": "healthy",
                    "result": result
                }
            except Exception as e:
                return {
                    "check": check_name,
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        self.health_checks.append(wrapped_health_check)
    
    async def initialize(self, settings=None, db_session_factory=None) -> bool:
        """Execute all initialization steps"""
        try:
            self.logger.info(f"Starting initialization for {self.service_name}")
            
            # Step 1: Validate configuration and dependencies
            if settings:
                try:
                    await validate_service_startup(
                        self.service_name, 
                        db_session_factory, 
                        settings
                    )
                except StartupValidationError as e:
                    raise ServiceInitializationError(f"Startup validation failed: {e}")
            
            # Step 2: Initialize service clients if settings available
            if settings and hasattr(settings, 'get_service_urls'):
                service_urls = settings.get_service_urls()
                if service_urls:
                    service_client_manager.initialize(
                        service_urls,
                        timeout=getattr(settings, 'request_timeout_seconds', 30),
                        max_retries=getattr(settings, 'max_retries', 3)
                    )
            
            # Step 3: Execute custom initialization steps
            for step in self.initialization_steps:
                await step()
            
            self.logger.info(f"Successfully initialized {self.service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.service_name}: {e}")
            raise
    
    async def cleanup(self):
        """Execute all cleanup steps"""
        self.logger.info(f"Starting cleanup for {self.service_name}")
        
        # Execute cleanup steps in reverse order
        for cleanup_step in reversed(self.cleanup_steps):
            await cleanup_step()
        
        self.logger.info(f"Completed cleanup for {self.service_name}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health_results = []
        
        # Execute all health checks
        for health_check in self.health_checks:
            result = await health_check()
            health_results.append(result)
        
        # Get service client health
        client_health = await service_client_manager.health_check_all()
        
        # Determine overall health
        unhealthy_checks = [r for r in health_results if r.get("status") != "healthy"]
        overall_healthy = len(unhealthy_checks) == 0 and client_health.get("overall_status") == "healthy"
        
        return {
            "service": self.service_name,
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": asyncio.get_event_loop().time(),
            "checks": health_results,
            "external_services": client_health,
            "unhealthy_checks": len(unhealthy_checks),
            "total_checks": len(health_results)
        }

# Factory function to create startup manager with common patterns
def create_service_startup_manager(
    service_name: str,
    settings=None,
    db_session_factory=None,
    custom_initialization: List[Callable] = None,
    custom_health_checks: List[Callable] = None
) -> ServiceStartupManager:
    """Factory function to create a configured startup manager"""
    
    manager = ServiceStartupManager(service_name)
    
    # Add custom initialization steps
    if custom_initialization:
        for init_func in custom_initialization:
            manager.add_initialization_step(init_func)
    
    # Add custom health checks
    if custom_health_checks:
        for health_func in custom_health_checks:
            manager.add_health_check(health_func)
    
    # Add common health checks
    if db_session_factory:
        async def database_health_check():
            """Check database connectivity"""
            try:
                async with db_session_factory() as session:
                    await session.execute("SELECT 1")
                return {"database": "connected"}
            except Exception as e:
                raise Exception(f"Database connection failed: {e}")
        
        manager.add_health_check(database_health_check, "database_connectivity")
    
    if settings:
        def configuration_health_check():
            """Check configuration health"""
            if hasattr(settings, 'get_configuration_health'):
                return settings.get_configuration_health()
            else:
                return {"configuration": "loaded"}
        
        manager.add_health_check(configuration_health_check, "configuration")
    
    return manager

# Context manager for service lifecycle
@asynccontextmanager
async def service_lifespan(startup_manager: ServiceStartupManager, settings=None, db_session_factory=None):
    """Context manager for complete service lifecycle management"""
    try:
        # Startup
        await startup_manager.initialize(settings, db_session_factory)
        yield startup_manager
    except Exception as e:
        logger.error(f"Service startup failed: {e}")
        raise
    finally:
        # Cleanup
        try:
            await startup_manager.cleanup()
        except Exception as e:
            logger.error(f"Service cleanup failed: {e}")

# Decorator for adding error handling to service endpoints
def handle_service_errors(fallback_response: Dict[str, Any] = None):
    """Decorator to add consistent error handling to service endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ServiceInitializationError as e:
                logger.error(f"Service initialization error in {func.__name__}: {e}")
                return {
                    "error": "Service initialization error",
                    "message": str(e),
                    "fallback": fallback_response
                }
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                return {
                    "error": "Internal service error",
                    "message": "An unexpected error occurred",
                    "fallback": fallback_response
                }
        return wrapper
    return decorator

# Utility functions for common startup patterns
async def initialize_database_connection(db_session_factory, service_name: str):
    """Initialize and validate database connection"""
    try:
        async with db_session_factory() as session:
            await session.execute("SELECT 1")
        logger.info(f"Database connection initialized for {service_name}")
    except Exception as e:
        raise ServiceInitializationError(f"Database initialization failed for {service_name}: {e}")

async def initialize_external_services(service_urls: Dict[str, str], service_name: str):
    """Initialize HTTP clients for external services"""
    try:
        service_client_manager.initialize(service_urls)
        logger.info(f"External service clients initialized for {service_name}")
    except Exception as e:
        raise ServiceInitializationError(f"External service initialization failed for {service_name}: {e}")

def create_fastapi_lifespan(startup_manager: ServiceStartupManager, settings=None, db_session_factory=None):
    """Create a FastAPI lifespan context manager"""
    
    @asynccontextmanager
    async def lifespan(app):
        # Startup
        try:
            await startup_manager.initialize(settings, db_session_factory)
            logger.info(f"FastAPI application started for {startup_manager.service_name}")
            yield
        except Exception as e:
            logger.error(f"FastAPI startup failed: {e}")
            raise
        finally:
            # Shutdown
            try:
                await startup_manager.cleanup()
                logger.info(f"FastAPI application shutdown completed for {startup_manager.service_name}")
            except Exception as e:
                logger.error(f"FastAPI shutdown failed: {e}")
    
    return lifespan