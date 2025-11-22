import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Default location: HuggingFace HQ (20 Jay Street, Brooklyn, NY)
DEFAULT_LAT = 40.7041
DEFAULT_LNG = -73.9867
DEFAULT_REGION = "US-NY-047"  # Brooklyn, NY

def get_bird_sightings(location: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent bird sightings near a location.
    
    Args:
        location: Location name or region code (e.g., "Glasgow, UK" or "GB-SCT")
        max_results: Maximum number of results to return
        
    Returns:
        List of bird sighting dicts with species, location, date info
    """
    logger.info(f"Getting bird sightings for location: {location or 'default (HF HQ)'}")
    
    # Mock data - structured like real eBird API
    # These are real corvid species that might be seen in Brooklyn/Glasgow
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
    
    # If location specified, adjust mock data accordingly
    if location and ("glasgow" in location.lower() or "scotland" in location.lower() or "GB" in location):
        # Glasgow-specific species
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