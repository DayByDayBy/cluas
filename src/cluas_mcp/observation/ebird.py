import os
import logging
from typing import List, Dict, Any
import requests

logger = logging.getLogger(__name__)

# Default location: HuggingFace HQ (20 Jay Street, Brooklyn, NY)
DEFAULT_LAT = 40.7041
DEFAULT_LNG = -73.9867
DEFAULT_REGION = "US-NY-047"  # Brooklyn, NY

EBIRD_BASE_URL = "https://api.ebird.org/v2"

# Location coordinates for known locations
LOCATION_COORDS = {
    "glasgow": {"lat": 55.8642, "lng": -4.2518, "region": "GB-SCT"},
    "brooklyn": {"lat": 40.6782, "lng": -73.9442, "region": "US-NY-047"},
    "seattle": {"lat": 47.6062, "lng": -122.3321, "region": "US-WA"},
    "tokyo": {"lat": 35.6762, "lng": 139.6503, "region": "JP"},
    "huggingface hq": {"lat": DEFAULT_LAT, "lng": DEFAULT_LNG, "region": DEFAULT_REGION},
}


def fetch_bird_sightings(location: str = None, max_results: int = 10, species: str = None) -> list[dict]:
    """
    Get recent bird sightings near a location using eBird API.
    """
    logger.info(f"Getting bird sightings for location: {location or 'default (HF HQ)'}")

    api_key = os.getenv("EBIRD_API_KEY")
    sightings: list[dict] = []

    if not api_key:
        logger.warning("EBIRD_API_KEY not found, using mock data")
        return _mock_sightings(location, max_results, species)

    try:
        headers = {"X-eBirdApiToken": api_key}

        location_lower = (location or "").lower().split(",")[0].strip()
        coords = LOCATION_COORDS.get(location_lower)

        if coords:
            url = f"{EBIRD_BASE_URL}/data/obs/geo/recent"
            params = {
                "lat": coords["lat"],
                "lng": coords["lng"],
                "maxResults": max_results,
                "dist": 25,
            }
        elif location and len(location) <= 12 and "-" in location:
            url = f"{EBIRD_BASE_URL}/data/obs/{location}/recent"
            params = {"maxResults": max_results}
        else:
            url = f"{EBIRD_BASE_URL}/data/obs/geo/recent"
            params = {
                "lat": DEFAULT_LAT,
                "lng": DEFAULT_LNG,
                "maxResults": max_results,
                "dist": 25,
            }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        sightings = response.json()
        logger.info(f"Retrieved {len(sightings)} sightings from eBird API")

        if species:   
            species_lower = species.lower()
            sightings = [
                s for s in sightings
                if species_lower in s.get("comName", "").lower() or species_lower in s.get("sciName", "").lower()
            ]
        return sightings

    except requests.exceptions.RequestException as e:
        logger.error(f"eBird API error: {e}")
        return _mock_sightings(location, max_results, species)



def _mock_sightings(location: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
    """Fallback mock data when API is unavailable."""
    # Glasgow-specific species
    if location and ("glasgow" in location.lower() or "scotland" in location.lower() or "GB" in location):
        mock_sightings = [
            {
                "speciesCode": "hoocro1",
                "comName": "Hooded Crow",
                "sciName": "Corvus cornix",
                "locId": "L999001",
                "locName": "Glasgow Green",
                "obsDt": "2024-11-23 14:00",
                "howMany": 15,
                "lat": 55.8470,
                "lng": -4.2380,
                "obsValid": True,
                "locationPrivate": False
            },
            {
                "speciesCode": "carcar",
                "comName": "Carrion Crow",
                "sciName": "Corvus corone",
                "locId": "L999002",
                "locName": "Kelvingrove Park",
                "obsDt": "2024-11-23 13:30",
                "howMany": 8,
                "lat": 55.8736,
                "lng": -4.2889,
                "obsValid": True,
                "locationPrivate": False
            },
            {
                "speciesCode": "eurmag",
                "comName": "Eurasian Magpie",
                "sciName": "Pica pica",
                "locId": "L999003",
                "locName": "Pollok Country Park",
                "obsDt": "2024-11-23 12:15",
                "howMany": 4,
                "lat": 55.8333,
                "lng": -4.3097,
                "obsValid": True,
                "locationPrivate": False
            },
            {
                "speciesCode": "comrav",
                "comName": "Common Raven",
                "sciName": "Corvus corax",
                "locId": "L999004",
                "locName": "Cathkin Braes",
                "obsDt": "2024-11-23 11:00",
                "howMany": 2,
                "lat": 55.8047,
                "lng": -4.2114,
                "obsValid": True,
                "locationPrivate": False
            },
            {
                "speciesCode": "jackda",
                "comName": "Western Jackdaw",
                "sciName": "Coloeus monedula",
                "locId": "L999005",
                "locName": "Glasgow Cathedral",
                "obsDt": "2024-11-23 10:45",
                "howMany": 20,
                "lat": 55.8625,
                "lng": -4.2336,
                "obsValid": True,
                "locationPrivate": False
            }
        ]
    else:
        # Default Brooklyn/NYC area mock data
        mock_sightings = [
            {
                "speciesCode": "amecro",
                "comName": "American Crow",
                "sciName": "Corvus brachyrhynchos",
                "locId": "L123456",
                "locName": "Brooklyn Bridge Park",
                "obsDt": "2024-11-23 14:30",
                "howMany": 12,
                "lat": 40.7041,
                "lng": -73.9867,
                "obsValid": True,
                "locationPrivate": False
            },
            {
                "speciesCode": "blujay",
                "comName": "Blue Jay",
                "sciName": "Cyanocitta cristata",
                "locId": "L123457",
                "locName": "Prospect Park",
                "obsDt": "2024-11-23 13:15",
                "howMany": 3,
                "lat": 40.6602,
                "lng": -73.9690,
                "obsValid": True,
                "locationPrivate": False
            },
            {
                "speciesCode": "fiscro",
                "comName": "Fish Crow",
                "sciName": "Corvus ossifragus",
                "locId": "L123458",
                "locName": "East River Waterfront",
                "obsDt": "2024-11-23 12:00",
                "howMany": 8,
                "lat": 40.7128,
                "lng": -73.9950,
                "obsValid": True,
                "locationPrivate": False
            },
            {
                "speciesCode": "comrav",
                "comName": "Common Raven",
                "sciName": "Corvus corax",
                "locId": "L789012",
                "locName": "Central Park North",
                "obsDt": "2024-11-23 11:45",
                "howMany": 2,
                "lat": 40.7969,
                "lng": -73.9519,
                "obsValid": True,
                "locationPrivate": False
            },
            {
                "speciesCode": "bkmag1",
                "comName": "Black-billed Magpie",
                "sciName": "Pica hudsonia",
                "locId": "L789013",
                "locName": "Green-Wood Cemetery",
                "obsDt": "2024-11-23 10:30",
                "howMany": 1,
                "lat": 40.6563,
                "lng": -73.9938,
                "obsValid": True,
                "locationPrivate": False
            }
        ]
    
    return mock_sightings[:max_results]


def format_sightings_for_display(sightings: List[Dict[str, Any]]) -> str:
    """Format sightings for character consumption."""
    if not sightings:
        return "No recent bird sightings found."
    
    output = []
    for sighting in sightings:
        count = sighting.get("howMany", "unknown number of")
        species = sighting.get("comName", "Unknown species")
        location = sighting.get("locName", "Unknown location")
        date = sighting.get("obsDt", "Unknown date")
        
        output.append(f"• {count} {species} at {location} ({date})")
    
    return "\n".join(output)