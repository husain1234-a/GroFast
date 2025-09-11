from firebase_admin import auth
from fastapi import HTTPException, status
from .config import initialize_firebase
import logging

logger = logging.getLogger(__name__)

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
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase ID token provided: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except auth.ExpiredIdTokenError as e:
        logger.warning(f"Expired Firebase ID token provided: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except auth.RevokedIdTokenError as e:
        logger.warning(f"Revoked Firebase ID token provided: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except auth.CertificateFetchError as e:
        logger.error(f"Firebase certificate fetch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable"
        )
    except auth.UserDisabledError as e:
        logger.warning(f"Disabled user attempted authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been disabled"
        )
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
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
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Google ID token provided: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except auth.ExpiredIdTokenError as e:
        logger.warning(f"Expired Google ID token provided: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except auth.RevokedIdTokenError as e:
        logger.warning(f"Revoked Google ID token provided: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication token has been revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed"
        )

async def get_user_by_uid(uid: str):
    """Get Firebase user by UID"""
    try:
        user = auth.get_user(uid)
        return user
    except auth.UserNotFoundError as e:
        logger.warning(f"Firebase user not found: {uid}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except Exception as e:
        logger.error(f"Failed to get Firebase user {uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )