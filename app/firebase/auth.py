from firebase_admin import auth
from fastapi import HTTPException, status
from .config import initialize_firebase

async def verify_firebase_token(id_token: str) -> dict:
    """Verify Firebase ID token and return user info"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            'uid': decoded_token['uid'],
            'phone': decoded_token.get('phone_number'),
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name')
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {str(e)}"
        )

async def verify_google_token(google_id_token: str) -> dict:
    """Verify Google ID token and return user info"""
    try:
        # Google ID tokens can be verified directly by Firebase
        decoded_token = auth.verify_id_token(google_id_token)
        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
            'provider': 'google.com'
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )

async def get_user_by_uid(uid: str):
    """Get Firebase user by UID"""
    try:
        user = auth.get_user(uid)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {str(e)}"
        )