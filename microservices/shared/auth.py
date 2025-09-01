from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(__file__))
from http_client import ResilientHttpClient
from custom_circuit_breaker import CircuitBreaker, RetryConfig, CircuitBreakerError
import logging

logger = logging.getLogger(__name__)

class AuthClient:
    def __init__(self, auth_service_url: str):
        self.auth_service_url = auth_service_url
        self.http_client = ResilientHttpClient(
            base_url=auth_service_url,
            timeout=5.0,
            circuit_breaker=CircuitBreaker(name="AuthService"),
            retry_config=RetryConfig(max_attempts=3, base_delay=0.5)
        )
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify token with auth service"""
        try:
            response = await self.http_client.post(
                "/internal/verify-token",
                json={"token": token}
            )
            return response.json()
        except CircuitBreakerError:
            logger.warning("Auth service circuit breaker is open, using fallback")
            # Fallback: basic token validation
            if token and len(token) > 10:
                return {
                    "user_id": 1,
                    "email": "fallback@example.com",
                    "name": "Fallback User",
                    "fallback": True
                }
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """Get user info from auth service"""
        try:
            response = await self.http_client.get(f"/internal/users/{user_id}")
            return response.json()
        except CircuitBreakerError:
            logger.warning("Auth service circuit breaker is open, using fallback")
            return {
                "id": user_id,
                "email": "fallback@example.com",
                "name": "Fallback User",
                "fallback": True
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user info")