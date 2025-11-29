
import requests
from typing import Optional

def check_weather(location: str) -> str:
    """
    Simple weather check - what any person might know.
    Returns casual awareness, not detailed observations.
    
    Args:
        location: City or region name
        
    Returns:
        Short string like "Currently 15°C and rainy in Seattle"
    """
    # Use simple weather API (OpenWeather, wttr.in, etc.)
    # Return concise string
    # Keep it lightweight - this isn't Crow's observation suite
    pass  # Implementation details


def check_local_weather(character) -> str:
    """
    Check weather at character's current location.
    Convenience wrapper for character.location.
    
    Args:
        character: Any Character instance with .location attribute
        
    Returns:
        Weather string for character's location
    """
    return check_weather(character.location)