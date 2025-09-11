import math
from typing import Tuple

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

def is_within_delivery_radius(user_lat: float, user_lon: float, store_lat: float = 28.6139, store_lon: float = 77.2090, radius_km: float = 10) -> bool:
    """Check if user is within delivery radius (default: Delhi coordinates)"""
    distance = calculate_distance(user_lat, user_lon, store_lat, store_lon)
    return distance <= radius_km

def estimate_delivery_time(distance_km: float) -> int:
    """Estimate delivery time in minutes based on distance"""
    # Base time: 15 minutes + 2 minutes per km
    base_time = 15
    travel_time = distance_km * 2
    return int(base_time + travel_time)