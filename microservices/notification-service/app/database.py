import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from database import DatabaseManager, Base
from .config import settings

db_manager = DatabaseManager(settings.database_url)

async def get_db():
    async for session in db_manager.get_db():
        yield session