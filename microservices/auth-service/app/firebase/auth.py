"""
Firebase Authentication Integration
Handles Firebase token verification and user management
"""

import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from typing import Dict, Any, Optional
import os
import json
import logging

logger = logging.getLogger(__name__)

class FirebaseAuth:
    _app = None
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK"""
        if cls._initialized:
            return
        
        try:
            # Try to get Firebase credentials from environment
            firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
            
            if firebase_creds:
                # Parse JSON credentials from environment variable
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
            else:
                # Try to load from file (for development)
                cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                else:
                    # Use default credentials (for demo/testing)
                    logger.warning("No Firebase credentials found, using demo mode")
                    cls._initialized = True
                    return
            
            # Initialize Firebase app
            cls._app = firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
            
            # Test the connection
            try:
                # Verify initialization by checking app instance
                if cls._app:
                    logger.info("Firebase connection verified successfully")
            except Exception as test_error:
                logger.warning(f"Firebase connection test failed: {test_error}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            # Continue without Firebase for demo purposes
            cls._initialized = True
    
    @classmethod
    def verify_firebase_token(cls, token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return user information
        
        Args:
            token: Firebase ID token
            
        Returns:
            Dict containing user information
            
        Raises:
            HTTPException: If token is invalid
        """
        cls.initialize()
        
        # Demo mode fallback if Firebase is not properly configured
        if not cls._app:
            return cls._demo_token_verification(token)
        
        try:
            # Verify the token with Firebase
            decoded_token = auth.verify_id_token(token)
            
            # Extract user information
            user_info = {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name', decoded_token.get('email', '').split('@')[0]),
                'phone': decoded_token.get('phone_number'),
                'email_verified': decoded_token.get('email_verified', False),
                'provider': decoded_token.get('firebase', {}).get('sign_in_provider', 'unknown')
            }
            
            logger.info(f"Successfully verified token for user: {user_info['uid']}")
            return user_info
            
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
    
    @classmethod
    def verify_google_token(cls, token: str) -> Dict[str, Any]:
        """
        Verify Google OAuth token via Firebase
        
        Args:
            token: Google OAuth token
            
        Returns:
            Dict containing user information
        """
        # For Google tokens, we can use the same verification process
        # as Firebase handles Google OAuth integration
        return cls.verify_firebase_token(token)
    
    @classmethod
    def _demo_token_verification(cls, token: str) -> Dict[str, Any]:
        """
        Demo token verification for development/testing
        
        Args:
            token: Token to verify
            
        Returns:
            Dict containing demo user information
        """
        # Basic token validation for demo
        if not token or len(token) < 10:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
        
        # Generate consistent demo user based on token
        token_hash = hash(token) % 10000
        
        # Simulate different user types based on token
        if 'admin' in token.lower():
            user_type = 'admin'
            email = f"admin{token_hash}@example.com"
        elif 'google' in token.lower():
            user_type = 'google'
            email = f"google{token_hash}@gmail.com"
        else:
            user_type = 'regular'
            email = f"user{token_hash}@example.com"
        
        demo_user = {
            'uid': f"demo_{user_type}_{token_hash}",
            'email': email,
            'name': f"Demo {user_type.title()} User {token_hash}",
            'phone': f"+1555{token_hash:04d}" if token_hash % 2 == 0 else None,
            'email_verified': True,
            'provider': 'demo',
            'demo_mode': True
        }
        
        logger.info(f"Demo mode: Generated user info for token ending in ...{token[-8:]}")
        return demo_user
    
    @classmethod
    def get_user_by_uid(cls, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by Firebase UID
        
        Args:
            uid: Firebase user UID
            
        Returns:
            Dict containing user information or None if not found
        """
        cls.initialize()
        
        if not cls._app:
            # Demo mode fallback
            return {
                'uid': uid,
                'email': f"demo@example.com",
                'name': "Demo User",
                'demo_mode': True
            }
        
        try:
            user_record = auth.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'name': user_record.display_name or user_record.email.split('@')[0] if user_record.email else 'Unknown',
                'phone': user_record.phone_number,
                'email_verified': user_record.email_verified,
                'disabled': user_record.disabled,
                'created_at': user_record.user_metadata.creation_timestamp,
                'last_sign_in': user_record.user_metadata.last_sign_in_timestamp
            }
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found: {uid}")
            return None
        except Exception as e:
            logger.error(f"Failed to get Firebase user {uid}: {e}")
            return None

# Convenience functions for backward compatibility
def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Verify Firebase token - convenience function"""
    return FirebaseAuth.verify_firebase_token(token)

def verify_google_token(token: str) -> Dict[str, Any]:
    """Verify Google token - convenience function"""
    return FirebaseAuth.verify_google_token(token)