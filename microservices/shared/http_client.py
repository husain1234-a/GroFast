import httpx
import asyncio
from typing import Optional, Dict, Any, Union
from .circuit_breaker import CircuitBreaker, RetryConfig, retry_with_backoff, CircuitBreakerError
import logging

logger = logging.getLogger(__name__)

class ResilientHttpClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_config: Optional[RetryConfig] = None,
        default_headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.circuit_breaker = circuit_breaker or CircuitBreaker(name=f"CB-{base_url}")
        self.retry_config = retry_config or RetryConfig()
        self.default_headers = default_headers or {}
        
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with timeout"""
        url = f"{self.base_url}{endpoint}"
        
        # Merge headers
        headers = {**self.default_headers}
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        # Set timeout
        kwargs.setdefault('timeout', self.timeout)
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
    
    async def _request_with_resilience(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """Make request with circuit breaker and retry logic"""
        
        async def make_request():
            return await self._make_request(method, endpoint, **kwargs)
        
        # Apply circuit breaker
        async def circuit_protected_request():
            return await self.circuit_breaker.call(make_request)
        
        # Apply retry logic
        return await retry_with_backoff(
            circuit_protected_request,
            self.retry_config
        )
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """GET request with resilience"""
        try:
            return await self._request_with_resilience(
                "GET",
                endpoint,
                params=params,
                headers=headers,
                **kwargs
            )
        except (CircuitBreakerError, httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"GET {self.base_url}{endpoint} failed: {e}")
            raise
    
    async def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """POST request with resilience"""
        try:
            return await self._request_with_resilience(
                "POST",
                endpoint,
                json=json,
                content=data,
                headers=headers,
                **kwargs
            )
        except (CircuitBreakerError, httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"POST {self.base_url}{endpoint} failed: {e}")
            raise
    
    async def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """PUT request with resilience"""
        try:
            return await self._request_with_resilience(
                "PUT",
                endpoint,
                json=json,
                content=data,
                headers=headers,
                **kwargs
            )
        except (CircuitBreakerError, httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"PUT {self.base_url}{endpoint} failed: {e}")
            raise
    
    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """DELETE request with resilience"""
        try:
            return await self._request_with_resilience(
                "DELETE",
                endpoint,
                headers=headers,
                **kwargs
            )
        except (CircuitBreakerError, httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"DELETE {self.base_url}{endpoint} failed: {e}")
            raise
    
    async def get_json(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request returning JSON with fallback"""
        try:
            response = await self.get(endpoint, **kwargs)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get JSON from {endpoint}: {e}")
            return {"error": "Service unavailable", "fallback": True}
    
    async def post_json(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST request returning JSON with fallback"""
        try:
            response = await self.post(endpoint, **kwargs)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to post JSON to {endpoint}: {e}")
            return {"error": "Service unavailable", "fallback": True}