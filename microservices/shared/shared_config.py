# Shared configuration utilities
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, ValidationError, validator
from typing import List, Optional, Dict, Any
import os
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration validation fails"""
    def __init__(self, message: str, missing_vars: List[str] = None, invalid_vars: Dict[str, str] = None):
        super().__init__(message)
        self.missing_vars = missing_vars or []
        self.invalid_vars = invalid_vars or {}

class BaseServiceSettings(BaseSettings, ABC):
    """Base settings for all microservices with enhanced error handling"""
    model_config = ConfigDict(
        extra='ignore',
        env_file=os.path.join(os.path.dirname(__file__), '..', '..', '.env'),
        env_file_encoding='utf-8',
        validate_assignment=True
    )
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    
    # App Settings
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000"]
    log_level: str = "INFO"
    
    # Service identification
    service_name: Optional[str] = None
    service_version: str = "1.0.0"
    
    def __init__(self, **kwargs):
        """Initialize settings with comprehensive validation and error handling"""
        try:
            super().__init__(**kwargs)
            self._post_init_validation()
            self._log_configuration_status()
        except ValidationError as e:
            self._handle_validation_error(e)
            raise
        except Exception as e:
            self._handle_unexpected_error(e)
            raise
    
    def _post_init_validation(self):
        """Additional validation after Pydantic validation"""
        # Validate JWT secret strength
        if len(self.jwt_secret_key) < 32:
            logger.warning("JWT secret key is shorter than recommended 32 characters")
        
        # Validate database URL format
        if not any(self.database_url.startswith(prefix) for prefix in ['postgresql://', 'postgresql+asyncpg://', 'sqlite://']):
            raise ConfigurationError(
                f"Invalid database URL format: {self.database_url[:20]}...",
                invalid_vars={"database_url": "Must be a valid database URL"}
            )
        
        # Validate Redis URL format
        if not self.redis_url.startswith('redis://'):
            logger.warning(f"Redis URL format may be invalid: {self.redis_url[:20]}...")
    
    def _handle_validation_error(self, error: ValidationError):
        """Handle Pydantic validation errors with detailed logging"""
        missing_vars = []
        invalid_vars = {}
        
        for err in error.errors():
            field = err['loc'][0] if err['loc'] else 'unknown'
            error_type = err['type']
            
            if error_type == 'missing':
                missing_vars.append(field)
            else:
                invalid_vars[field] = err['msg']
        
        error_msg = f"Configuration validation failed for {self.get_service_name()}"
        if missing_vars:
            error_msg += f"\nMissing required variables: {', '.join(missing_vars)}"
        if invalid_vars:
            error_msg += f"\nInvalid variables: {', '.join(f'{k}: {v}' for k, v in invalid_vars.items())}"
        
        logger.error(error_msg)
        
        # Create detailed configuration error
        config_error = ConfigurationError(error_msg, missing_vars, invalid_vars)
        
        # Log remediation suggestions
        self._log_remediation_suggestions(missing_vars, invalid_vars)
        
        raise config_error
    
    def _handle_unexpected_error(self, error: Exception):
        """Handle unexpected configuration errors"""
        error_msg = f"Unexpected configuration error for {self.get_service_name()}: {str(error)}"
        logger.error(error_msg, exc_info=True)
        raise ConfigurationError(error_msg)
    
    def _log_configuration_status(self):
        """Log successful configuration loading"""
        service_name = self.get_service_name()
        logger.info(f"Configuration loaded successfully for {service_name}")
        
        # Log non-sensitive configuration details
        config_summary = {
            "service_name": service_name,
            "service_version": self.service_version,
            "debug_mode": self.debug,
            "log_level": self.log_level,
            "cors_origins_count": len(self.cors_origins),
            "database_configured": bool(self.database_url),
            "redis_configured": bool(self.redis_url),
            "jwt_configured": bool(self.jwt_secret_key)
        }
        
        logger.info(f"Configuration summary: {config_summary}")
    
    def _log_remediation_suggestions(self, missing_vars: List[str], invalid_vars: Dict[str, str]):
        """Log suggestions for fixing configuration issues"""
        if missing_vars:
            logger.info("To fix missing variables:")
            for var in missing_vars:
                logger.info(f"  - Set environment variable: {var}")
                
        if invalid_vars:
            logger.info("To fix invalid variables:")
            for var, issue in invalid_vars.items():
                logger.info(f"  - Fix {var}: {issue}")
        
        logger.info("Check .env.template for required variable formats")
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Return the service name for logging and identification"""
        pass
    
    def get_critical_vars(self) -> List[str]:
        """Return list of critical environment variables that must be set"""
        return ["database_url", "redis_url", "jwt_secret_key"]
    
    def get_optional_vars(self) -> List[str]:
        """Return list of optional environment variables with graceful degradation"""
        return ["debug", "log_level", "cors_origins"]
    
    def validate_critical_configuration(self) -> bool:
        """Validate that all critical configuration is present and valid"""
        try:
            critical_vars = self.get_critical_vars()
            for var in critical_vars:
                value = getattr(self, var, None)
                if not value:
                    logger.error(f"Critical configuration missing: {var}")
                    return False
            
            logger.info("All critical configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Critical configuration validation failed: {e}")
            return False
    
    def get_configuration_health(self) -> Dict[str, Any]:
        """Return configuration health status for health checks"""
        critical_vars = self.get_critical_vars()
        optional_vars = self.get_optional_vars()
        
        critical_status = {}
        optional_status = {}
        
        for var in critical_vars:
            value = getattr(self, var, None)
            critical_status[var] = "configured" if value else "missing"
        
        for var in optional_vars:
            value = getattr(self, var, None)
            optional_status[var] = "configured" if value else "default"
        
        overall_health = "healthy" if all(status == "configured" for status in critical_status.values()) else "unhealthy"
        
        return {
            "overall_health": overall_health,
            "service_name": self.get_service_name(),
            "critical_configuration": critical_status,
            "optional_configuration": optional_status,
            "configuration_source": "environment_variables"
        }