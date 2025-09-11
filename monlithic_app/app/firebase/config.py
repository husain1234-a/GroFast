import firebase_admin
from firebase_admin import credentials, auth
from ..config.settings import settings
import os

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        if os.path.exists(settings.firebase_credentials_path):
            cred = credentials.Certificate(settings.firebase_credentials_path)
        else:
            # For production, use environment variables
            cred = credentials.ApplicationDefault()
        
        firebase_admin.initialize_app(cred, {
            'projectId': settings.firebase_project_id,
        })

# Call initialization
initialize_firebase()