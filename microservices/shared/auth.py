import httpx
from fastapi import HTTPException, status
from typing import Optional

class AuthClient:
    def __init__(self, auth_service_url: str):
        self.auth_service_url = auth_service_url
    
    async def verify_token(self, token: str) -> dict:
        """Verify token with auth service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.auth_service_url}/internal/verify-token",
                    json={"token": token}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(status_code=401, detail="Invalid token")
            except Exception as e:
                raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def get_user_info(self, user_id: int) -> dict:
        """Get user info from auth service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.auth_service_url}/internal/users/{user_id}")
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(status_code=404, detail="User not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail="Failed to get user info")