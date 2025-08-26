from fastapi import APIRouter, Request
import httpx
from ..config import settings

router = APIRouter()

@router.post("/fcm")
async def send_fcm_notification(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.notification_service_url}/notifications/fcm",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()