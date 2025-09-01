import httpx
import asyncio
import time
from typing import Dict, Any, Optional, Union, List
from enum import Enum
import sys
import os
sys.path.append(os.path.dirname(__file__))
from custom_circuit_breaker import CircuitBreaker, RetryConfig, CircuitBreakerError
import logging
import json

logger = logging.getLogger(__name__)

class ServiceError(Exception):
    """Base exception for service communication errors"""
    def __init__(self, message: str, service_name: str = None, status_code: int = None, response_body: str = None):
        super().__init__(message)
        self.service_name = service_name
        self.status_code = status_code
        self.response_body = response_body

class ServiceUnavailableError(ServiceError):
    """Raised when a service is temporarily unavailable"""
    pass

class ServiceTimeoutError(ServiceError):
    """Raised when a service request times out"""
    pass

class ServiceAuthenticationError(ServiceError):
    """Raised when service authentication fails"""
    pass

class ServiceValidationError(ServiceError):
    """Raised when service request validation fails"""
    pass

class RetryStrategy(Enum):
    """Retry strategies for failed requests"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"

class EnhancedRetryConfig:
    """Enhanced retry configuration with multiple strategies"""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        retryable_status_codes: List[int] = None,
        retryable_exceptions: List[type] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.retryable_status_codes = retryable_status_codes or [502, 503, 504, 429]
        self.retryable_exceptions = retryable_exceptions or [
            httpx.TimeoutException, 
            httpx.ConnectError, 
            httpx.NetworkError
        ]
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (2 ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * attempt
        else:  # FIXED_DELAY
            delay = self.base_delay
        
        return min(delay, self.max_delay)

class ResilientHttpClient:
    """Enhanced HTTP client with comprehensive error handling and resilience patterns"""
    
    def __init__(
        self, 
        base_url: str = "", 
        service_name: str = "unknown",
        timeout: float = 30.0,
        circuit_breaker: Optional[CircuitBreaker] = None, 
        retry_config: Optional[EnhancedRetryConfig] = None,
        default_headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.service_name = service_name
        self.timeout = timeout
        self.circuit_breaker = circuit_breaker
        self.retry_config = retry_config or EnhancedRetryConfig()
        self.default_headers = default_headers or {}
        
        # Request tracking
        self._request_count = 0
        self._error_count = 0
        self._last_success_time = None
        
        logger.info(f"Initialized HTTP client for {service_name} at {base_url}")
    
    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Merge default headers with request-specific headers"""
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged
    
    def _classify_error(self, response: httpx.Response = None, exception: Exception = None) -> ServiceError:
        """Classify errors into appropriate service error types"""
        if exception:
            if isinstance(exception, httpx.TimeoutException):
                return ServiceTimeoutError(
                    f"Request to {self.service_name} timed out after {self.timeout}s",
                    service_name=self.service_name
                )
            elif isinstance(exception, (httpx.ConnectError, httpx.NetworkError)):
                return ServiceUnavailableError(
                    f"Unable to connect to {self.service_name}: {str(exception)}",
                    service_name=self.service_name
                )
            else:
                return ServiceError(
                    f"Unexpected error communicating with {self.service_name}: {str(exception)}",
                    service_name=self.service_name
                )
        
        if response:
            status_code = response.status_code
            response_text = response.text[:500] if response.text else "No response body"
            
            if status_code == 401:
                return ServiceAuthenticationError(
                    f"Authentication failed for {self.service_name}",
                    service_name=self.service_name,
                    status_code=status_code,
                    response_body=response_text
                )
            elif status_code == 400:
                return ServiceValidationError(
                    f"Request validation failed for {self.service_name}",
                    service_name=self.service_name,
                    status_code=status_code,
                    response_body=response_text
                )
            elif status_code in [502, 503, 504]:
                return ServiceUnavailableError(
                    f"{self.service_name} is temporarily unavailable (HTTP {status_code})",
                    service_name=self.service_name,
                    status_code=status_code,
                    response_body=response_text
                )
            elif status_code == 429:
                return ServiceUnavailableError(
                    f"{self.service_name} rate limit exceeded (HTTP {status_code})",
                    service_name=self.service_name,
                    status_code=status_code,
                    response_body=response_text
                )
            else:
                return ServiceError(
                    f"{self.service_name} returned HTTP {status_code}",
                    service_name=self.service_name,
                    status_code=status_code,
                    response_body=response_text
                )
        
        return ServiceError(f"Unknown error communicating with {self.service_name}")
    
    def _should_retry(self, error: ServiceError, attempt: int) -> bool:
        """Determine if request should be retried"""
        if attempt >= self.retry_config.max_attempts:
            return False
        
        # Don't retry authentication or validation errors
        if isinstance(error, (ServiceAuthenticationError, ServiceValidationError)):
            return False
        
        # Retry service unavailable and timeout errors
        if isinstance(error, (ServiceUnavailableError, ServiceTimeoutError)):
            return True
        
        # Check status code if available
        if error.status_code and error.status_code in self.retry_config.retryable_status_codes:
            return True
        
        return False
    
    async def _execute_with_retry(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> httpx.Response:
        """Execute HTTP request with retry logic"""
        full_url = f"{self.base_url}{url}" if url.startswith('/') else f"{self.base_url}/{url}"
        
        # Check circuit breaker
        if self.circuit_breaker and self.circuit_breaker.is_open:
            raise CircuitBreakerError(f"Circuit breaker is open for {self.service_name}")
        
        last_error = None
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            self._request_count += 1
            
            try:
                logger.debug(f"Attempt {attempt}/{self.retry_config.max_attempts} - {method} {full_url}")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, full_url, **kwargs)
                    
                    # Check for HTTP errors
                    if response.status_code >= 400:
                        error = self._classify_error(response=response)
                        
                        if self._should_retry(error, attempt):
                            last_error = error
                            logger.warning(f"Retryable error on attempt {attempt}: {error}")
                            
                            if attempt < self.retry_config.max_attempts:
                                delay = self.retry_config.get_delay(attempt)
                                logger.debug(f"Waiting {delay}s before retry")
                                await asyncio.sleep(delay)
                                continue
                        
                        # Non-retryable error or max attempts reached
                        self._error_count += 1
                        if self.circuit_breaker:
                            self.circuit_breaker.record_failure()
                        raise error
                    
                    # Success
                    self._last_success_time = time.time()
                    if self.circuit_breaker:
                        self.circuit_breaker.record_success()
                    
                    logger.debug(f"Successful {method} request to {self.service_name}")
                    return response
                    
            except Exception as e:
                error = self._classify_error(exception=e)
                
                if self._should_retry(error, attempt):
                    last_error = error
                    logger.warning(f"Retryable error on attempt {attempt}: {error}")
                    
                    if attempt < self.retry_config.max_attempts:
                        delay = self.retry_config.get_delay(attempt)
                        logger.debug(f"Waiting {delay}s before retry")
                        await asyncio.sleep(delay)
                        continue
                
                # Non-retryable error or max attempts reached
                self._error_count += 1
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                raise error
        
        # If we get here, all retries failed
        if last_error:
            raise last_error
        else:
            raise ServiceError(f"All retry attempts failed for {self.service_name}")
    
    async def get(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute GET request with error handling and retries"""
        merged_headers = self._merge_headers(headers)
        
        response = await self._execute_with_retry(
            "GET", 
            url, 
            headers=merged_headers,
            params=params,
            **kwargs
        )
        
        try:
            return response.json()
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response from {self.service_name}: {response.text[:200]}")
            return {"raw_response": response.text}
    
    async def post(
        self, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute POST request with error handling and retries"""
        merged_headers = self._merge_headers(headers)
        
        response = await self._execute_with_retry(
            "POST", 
            url, 
            headers=merged_headers,
            json=data,
            **kwargs
        )
        
        try:
            return response.json()
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response from {self.service_name}: {response.text[:200]}")
            return {"raw_response": response.text}
    
    async def put(
        self, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute PUT request with error handling and retries"""
        merged_headers = self._merge_headers(headers)
        
        response = await self._execute_with_retry(
            "PUT", 
            url, 
            headers=merged_headers,
            json=data,
            **kwargs
        )
        
        try:
            return response.json()
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response from {self.service_name}: {response.text[:200]}")
            return {"raw_response": response.text}
    
    async def delete(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute DELETE request with error handling and retries"""
        merged_headers = self._merge_headers(headers)
        
        response = await self._execute_with_retry(
            "DELETE", 
            url, 
            headers=merged_headers,
            **kwargs
        )
        
        try:
            return response.json()
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response from {self.service_name}: {response.text[:200]}")
            return {"raw_response": response.text}
    
    async def health_check(self, health_endpoint: str = "/health") -> Dict[str, Any]:
        """Perform health check on the service"""
        try:
            response = await self.get(health_endpoint)
            return {
                "service": self.service_name,
                "status": "healthy",
                "response": response,
                "response_time_ms": None  # Could be enhanced to track timing
            }
        except ServiceError as e:
            return {
                "service": self.service_name,
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get client statistics for monitoring"""
        return {
            "service_name": self.service_name,
            "base_url": self.base_url,
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "last_success_time": self._last_success_time,
            "circuit_breaker_open": self.circuit_breaker.is_open if self.circuit_breaker else False
        }

# Factory function for creating configured HTTP clients
def create_service_client(
    service_name: str,
    base_url: str,
    timeout: float = 30.0,
    max_retries: int = 3,
    enable_circuit_breaker: bool = True
) -> ResilientHttpClient:
    """Factory function to create a configured HTTP client for a service"""
    
    # Create circuit breaker if enabled
    circuit_breaker = None
    if enable_circuit_breaker:
        circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_duration=60,
            expected_exception=ServiceError
        )
    
    # Create retry configuration
    retry_config = EnhancedRetryConfig(
        max_attempts=max_retries,
        base_delay=1.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF
    )
    
    # Default headers
    default_headers = {
        "Content-Type": "application/json",
        "User-Agent": f"microservice-client/{service_name}"
    }
    
    return ResilientHttpClient(
        base_url=base_url,
        service_name=service_name,
        timeout=timeout,
        circuit_breaker=circuit_breaker,
        retry_config=retry_config,
        default_headers=default_headers
    )