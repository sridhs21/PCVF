import logging
import os
from typing import Tuple, Dict, Optional
import requests


logger = logging.getLogger(__name__)


_geocode_cache = {}


COMMON_CITIES = {
    'new york': (40.7128, -74.0060),
    'los angeles': (34.0522, -118.2437),
    'chicago': (41.8781, -87.6298),
    'houston': (29.7604, -95.3698),
    'phoenix': (33.4484, -112.0740),
    'philadelphia': (39.9526, -75.1652),
    'san antonio': (29.4241, -98.4936),
    'san diego': (32.7157, -117.1611),
    'dallas': (32.7767, -96.7970),
    'san jose': (37.3382, -121.8863),
    'austin': (30.2672, -97.7431),
    'jacksonville': (30.3322, -81.6557),
    'san francisco': (37.7749, -122.4194),
    'columbus': (39.9612, -82.9988),
    'fort worth': (32.7555, -97.3308),
    'indianapolis': (39.7684, -86.1581),
    'charlotte': (35.2271, -80.8431),
    'seattle': (47.6062, -122.3321),
    'denver': (39.7392, -104.9903),
    'washington': (38.9072, -77.0369),
    'boston': (42.3601, -71.0589),
    'nashville': (36.1627, -86.7816),
    'baltimore': (39.2904, -76.6122),
    'oklahoma city': (35.4676, -97.5164),
    'portland': (45.5051, -122.6750),
    'las vegas': (36.1699, -115.1398),
    'detroit': (42.3314, -83.0458),
    'memphis': (35.1495, -90.0490),
    'louisville': (38.2527, -85.7585),
    'milwaukee': (43.0389, -87.9065)
}

def geocode_location(location: str) -> Tuple[Optional[float], Optional[float]]:
    if not location:
        return None, None
        
    location_key = location.lower().strip()
    if location_key in _geocode_cache:
        logger.debug(f"Using cached coordinates for {location}")
        return _geocode_cache[location_key]
    
    if ',' in location and len(location.split(',')) == 2:
        parts = location.split(',')
        try:
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                _geocode_cache[location_key] = (lat, lng)
                return lat, lng
        except ValueError:
            pass  
    
    try:
        logger.info(f"Geocoding location with Nominatim: {location}")
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "PetCare-Vet-Finder/1.0"  
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                _geocode_cache[location_key] = (lat, lng)
                logger.info(f"Successfully geocoded {location} to {lat}, {lng}")
                return lat, lng
    except Exception as e:
        logger.warning(f"Error using Nominatim for {location}: {e}")
    
    coords = get_default_coordinates(location)
    if coords[0] is not None:
        _geocode_cache[location_key] = coords
        return coords
    
    logger.error(f"All geocoding methods failed for {location}")
    return None, None

def get_default_coordinates(location: str) -> Tuple[Optional[float], Optional[float]]:
    if not location:
        return None, None
        
    location_lower = location.lower().strip()
    if location_lower in COMMON_CITIES:
        logger.info(f"Using default coordinates for {location}")
        return COMMON_CITIES[location_lower]
    
    for city, coords in COMMON_CITIES.items():
        if city in location_lower or location_lower in city:
            logger.info(f"Using partial match default coordinates for {location} (matched with {city})")
            return coords
            
    parts = [p.strip() for p in location_lower.split(',')]
    for part in parts:
        if part in COMMON_CITIES:
            logger.info(f"Using city part match default coordinates for {location} (matched with {part})")
            return COMMON_CITIES[part]
    
    return None, None

def get_formatted_address(lat: float, lng: float) -> str:
    if lat is None or lng is None:
        return ""
        
    try:
        logger.info(f"Reverse geocoding coordinates: {lat}, {lng}")
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "PetCare-Vet-Finder/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "display_name" in data:
                return data["display_name"]
    except Exception as e:
        logger.warning(f"Error reverse geocoding {lat}, {lng}: {e}")
    
    return ""