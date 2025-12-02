"""
Shared location coordinates for agent locations.
Extracted from check_local_weather.py for reuse across modules.
"""
from typing import Dict, TypedDict

class LocationCoords(TypedDict):
    lat: float
    lon: float
    country: str

# Agent location coordinates
LOCATION_COORDS: Dict[str, LocationCoords] = {
    "Glasgow, Scotland": {"lat": 55.8642, "lon": -4.2518, "country": "UK"},
    "Brooklyn, NY": {"lat": 40.6782, "lon": -73.9442, "country": "US"},
    "Seattle, WA": {"lat": 47.6062, "lon": -122.3321, "country": "US"},
    "Tokyo, Japan": {"lat": 35.6762, "lon": 139.6503, "country": "JP"},
}

