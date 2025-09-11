from supabase import create_client, Client
from ..config.settings import settings
from typing import Dict, Any

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
    
    def insert_delivery_location(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert delivery location for real-time tracking"""
        try:
            result = self.client.table('delivery_locations').insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Error inserting delivery location: {e}")
            return {}
    
    def update_delivery_location(self, delivery_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update delivery location"""
        try:
            result = self.client.table('delivery_locations').update(data).eq('delivery_id', delivery_id).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Error updating delivery location: {e}")
            return {}
    
    def get_delivery_location(self, delivery_id: int) -> Dict[str, Any]:
        """Get current delivery location"""
        try:
            result = self.client.table('delivery_locations').select('*').eq('delivery_id', delivery_id).order('timestamp', desc=True).limit(1).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Error getting delivery location: {e}")
            return {}

# Global instance
supabase_client = SupabaseClient()