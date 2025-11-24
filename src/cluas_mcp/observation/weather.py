import os
import logging
import requests

logger = logging.getLogger(__name__)

LOCATION_COORDS = {
    "glasgow": {"lat": 55.8642, "lon": -4.2518},
    "brooklyn": {"lat": 40.6782, "lon": -73.9442},
    "seattle": {"lat": 47.6062, "lon": -122.3321},
    "tokyo": {"lat": 35.6762, "lon": 139.6503}
}

def get_weather_patterns(location: str = "global", timeframe: str = "recent") -> dict:
    """
    Get weather using OpenWeatherMap API.
    Free tier: 1,000 calls/day, 60 calls/minute
    """
    api_key = os.getenv("OPENWEATHER_KEY")
    
    if not api_key:
        logger.warning("OPENWEATHER_KEY not found, using mock data")
        return _mock_weather(location, timeframe)
    
    try:
        # Try to match location to character locations first
        location_lower = location.lower().split(",")[0].strip()
        coords = LOCATION_COORDS.get(location_lower)
        
        if coords:
            # Use coordinates for more accurate results
            params = {
                "lat": coords["lat"],
                "lon": coords["lon"],
                "appid": api_key,
                "units": "metric"
            }
        else:
            # Fall back to city name
            params = {
                "q": location,
                "appid": api_key,
                "units": "metric"
            }
        
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "location": location,
            "timeframe": timeframe,
            "patterns": {
                "average_temperature": data["main"]["temp"],
                "temperature_unit": "celsius",
                "feels_like": data["main"]["feels_like"],
                "precipitation": 0,  # Current weather doesn't include this
                "precipitation_unit": "mm",
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_unit": "m/s",
                "conditions": data["weather"][0]["description"],
                "description": f"Current weather in {location}: {data['weather'][0]['description']}, {data['main']['temp']}°C (feels like {data['main']['feels_like']}°C), humidity {data['main']['humidity']}%"
            },
            "source": "openweathermap"
        }
    
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return _mock_weather(location, timeframe)

def _mock_weather(location: str, timeframe: str) -> dict:
    """Fallback mock"""
    return "Weather is the same as always."
  