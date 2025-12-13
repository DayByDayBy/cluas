import os
import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

CITY_LOCATIONS = {
    "new york": [
        ("Division Street", 662),
        ("E Houston St between Clinton St & Attorney St", 4727343),
    ],
    "glasgow": [
        ("Glasgow Kerbside", 2320),
        ("Glasgow Great Western Road", 2372),
        ("Glasgow High Street", 2571),
        ("Glasgow Townhead", 2574),
    ],
    "seattle": [
        ("Seattle-10th & Welle", 931),
        ("S Lane St", 1235989),
    ],
    "tokyo": [
        ("Kunitachi", 1214854),
        ("Fuchu", 1215248),
        ("Hino", 1215329),
    ],
}


def fetch_air_quality(city: str, parameter: str = "pm25", limit: int = 5) -> Dict[str, Any]:
    """
    Fetch air quality data from OpenAQ API.
    
    Args:
        city: City name (e.g., "tokyo", "glasgow", "new york", "seattle")
        parameter: Air quality parameter (default: pm25)
        limit: Number of measurements per location
        
    Returns:
        Dictionary with air quality data or error info
    """
    api_key = os.getenv("OPEN_AQ_KEY")
    
    if not api_key:
        logger.warning("OPEN_AQ_KEY not found, returning error")
        return {"error": "OPEN_AQ_KEY not configured", "city": city}
    
    city_lower = city.lower().strip()
    locations = CITY_LOCATIONS.get(city_lower)
    
    if not locations:
        available = ", ".join(CITY_LOCATIONS.keys())
        return {
            "error": f"City '{city}' not found",
            "available_cities": available,
            "city": city
        }
    
    results = []
    for location_name, location_id in locations:
        try:
            response = requests.get(
                "https://api.openaq.org/v3/measurements",
                params={
                    "location_id": location_id,
                    "parameter": parameter,
                    "limit": limit,
                    "sort": "desc"
                },
                headers={
                    "Accept": "application/json",
                    "X-API-Key": api_key
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json().get("results", [])
            
            results.append({
                "location_name": location_name,
                "location_id": location_id,
                "measurements": data
            })
        except Exception as e:
            logger.error(f"Error fetching {location_name}: {e}")
            results.append({
                "location_name": location_name,
                "location_id": location_id,
                "error": str(e)
            })
    
    return {
        "city": city,
        "parameter": parameter,
        "locations": results,
        "source": "openaq"
    }