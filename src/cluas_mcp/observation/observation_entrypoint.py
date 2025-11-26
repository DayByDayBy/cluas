import logging
from typing import Optional
from src.cluas_mcp.observation.ebird import fetch_bird_sightings, format_sightings_for_display
from src.cluas_mcp.observation.weather import fetch_weather_patterns
from src.cluas_mcp.observation.airquality import fetch_air_quality
from src.cluas_mcp.observation.moon_phase import fetch_moon_phase
from src.cluas_mcp.observation.sunrise_sunset import fetch_sunrise_sunset
from src.cluas_mcp.common.observation_memory import ObservationMemory

logger = logging.getLogger(__name__)

def get_bird_sightings(location: str = "HuggingFace HQ, Brooklyn, NY") -> dict:
    """
    Get recent bird sightings near a location.
    Args:
        location: Location to search (defaults to HF HQ)
    Returns:
        Dictionary with sightings data
    """
    logger.info(f"Bird sightings tool called for: {location}")
    
    sightings = fetch_bird_sightings(location)
    formatted = format_sightings_for_display(sightings)
    
    return {
        "location": location,
        "sightings": sightings,
        "formatted": formatted,
        "count": len(sightings)
    }
    
    
def get_weather_patterns(location: str = "global", timeframe: str = "recent") -> dict:
    """
    Get weather pattern data.
    
    TODO: Implement full weather pattern functionality using a weather API.
    
    Args:
        location: Location to get weather for (e.g., "global", "US", "California")
        timeframe: Timeframe for data (e.g., "recent", "weekly", "monthly")
        
    Returns:
        Dictionary with weather pattern data
    """
    logger.info("Getting weather patterns for location: %s, timeframe: %s", location, timeframe)
    
    if location:
        return fetch_weather_patterns(location, timeframe)
    else: 
    # Mock structured data
        return {
            "location": location,
            "timeframe": timeframe,
            "patterns": {
                "average_temperature": 15.5,
                "temperature_unit": "celsius",
                "precipitation": 25.0,
                "precipitation_unit": "mm",
                "humidity": 65,
                "wind_speed": 12.5,
                "wind_unit": "km/h",
                "description": f"Mock weather pattern data for {location} over {timeframe}. Real implementation would fetch actual weather data from a weather API."
            },
            "source": "mock_data"
        }


def get_air_quality(city: str = "Tokyo", parameter: str = "pm25") -> dict:
    """
    Get air quality data for a city.
    
    Args:
        city: City to check (available: new york, glasgow, seattle, tokyo)
        parameter: Air quality parameter (default: pm25)
        
    Returns:
        Dictionary with air quality measurements
    """
    logger.info(f"Air quality tool called for: {city}, parameter: {parameter}")
    return fetch_air_quality(city, parameter)


def get_moon_phase(date: Optional[str] = None) -> dict:
    """Get current moon phase."""
    logger.info(f"Getting moon phase for date: {date}")
    return fetch_moon_phase(date)

def get_sun_times(location: str, date: Optional[str] = None) -> dict:
    """Get sunrise/sunset times for location."""
    logger.info(f"Getting sun times for {location}, date: {date}")
    return fetch_sunrise_sunset(location, date)

def analyze_temporal_patterns(obs_type: str, location: Optional[str] = None, days: int = 30) -> dict:
    """Analyze patterns from stored observations."""
    memory = ObservationMemory(location=location)
    return memory.analyze_patterns(obs_type, location, days)

# def analyze_temporal_patterns(data_type: str, location: str = "global") -> dict:
#     """
#     Analyze patterns over time.
    
#     TODO: Implement full temporal pattern analysis functionality.
    
#     Args:
#         data_type: Type of data to analyze (e.g., "bird_sightings", "weather", "behavior")
#         location: Location to analyze patterns for
        
#     Returns:
#         Dictionary with temporal pattern analysis
#     """
#     logger.info("Analyzing temporal patterns for data_type: %s, location: %s", data_type, location)
    
#     # Mock structured data
#     return {
#         "data_type": data_type,
#         "location": location,
#         "analysis": {
#             "trend": "stable",
#             "seasonality": "moderate",
#             "peak_periods": ["spring", "fall"],
#             "description": f"Mock temporal pattern analysis for {data_type} in {location}. Real implementation would perform actual statistical analysis on historical data.",
#             "confidence": 0.75
#         },
#         "time_range": "2023-01-01 to 2024-01-15",
#         "source": "mock_data"
#     }



