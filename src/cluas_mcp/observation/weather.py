import os
import logging
import requests

logger = logging.getLogger(__name__)

LOCATION_COORDS = {
    "glasgow": {"lat": 55.8642, "lon": -4.2518, "country": "UK"},
    "brooklyn": {"lat": 40.6782, "lon": -73.9442, "country": "US"},
    "seattle": {"lat": 47.6062, "lon": -122.3321, "country": "US"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "country": "JP"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "country": "US"},
}

def fetch_weather_patterns(location: str = "global", timeframe: str = "recent") -> dict:
    """
    Get weather using OpenWeatherMap API, with NWS fallback for US locations.
    OpenWeatherMap free tier: 1,000 calls/day, 60 calls/minute
    NWS API: Free, no key required, US only
    """
    api_key = os.getenv("OPENWEATHER_KEY")
    location_lower = location.lower().split(",")[0].strip()
    coords = LOCATION_COORDS.get(location_lower)
    
    # Try OpenWeatherMap first if we have a key
    if api_key:
        result = _fetch_openweathermap(location, location_lower, coords, api_key, timeframe)
        if result:
            return result
    
    # Fallback to NWS for US locations (free, no API key)
    if coords and coords.get("country") == "US":
        result = _fetch_nws(location, coords, timeframe)
        if result:
            return result
    elif not coords:
        # Try to detect if it's a US location by name
        us_indicators = ["us", "usa", "united states", "america"]
        if any(ind in location.lower() for ind in us_indicators):
            # Could attempt geocoding here, but for now fall through to mock
            pass
    
    logger.warning(f"No weather API available for {location}, using mock data")
    return _mock_weather(location, timeframe)


def _fetch_openweathermap(location: str, location_lower: str, coords: dict, api_key: str, timeframe: str) -> dict:
    """Fetch weather from OpenWeatherMap API."""
    try:
        if coords:
            params = {
                "lat": coords["lat"],
                "lon": coords["lon"],
                "appid": api_key,
                "units": "metric"
            }
        else:
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
                "precipitation": 0,
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
        logger.warning(f"OpenWeatherMap API error: {e}")
        return None


def _fetch_nws(location: str, coords: dict, timeframe: str) -> dict:
    """
    Fetch weather from National Weather Service API (US only, free, no key required).
    See: https://api.weather.gov/
    """
    try:
        # NWS requires a User-Agent header
        headers = {
            "User-Agent": "(cluas-weather-client, contact@example.com)",
            "Accept": "application/geo+json"
        }
        
        # Step 1: Get the forecast grid endpoint for these coordinates
        points_url = f"https://api.weather.gov/points/{coords['lat']},{coords['lon']}"
        points_response = requests.get(points_url, headers=headers, timeout=10)
        points_response.raise_for_status()
        points_data = points_response.json()
        
        # Step 2: Get the current observation station
        forecast_url = points_data["properties"]["forecast"]
        
        # Step 3: Get the forecast
        forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        # Get the current period (first in the list)
        current = forecast_data["properties"]["periods"][0]
        
        # NWS uses Fahrenheit by default, convert to Celsius
        temp_f = current["temperature"]
        temp_c = round((temp_f - 32) * 5 / 9, 1)
        
        # Parse wind speed (format: "5 mph" or "5 to 10 mph")
        wind_str = current.get("windSpeed", "0 mph")
        wind_parts = wind_str.replace(" mph", "").split(" to ")
        wind_mph = float(wind_parts[0]) if wind_parts else 0
        wind_ms = round(wind_mph * 0.44704, 1)  # Convert to m/s
        
        return {
            "location": location,
            "timeframe": timeframe,
            "patterns": {
                "average_temperature": temp_c,
                "temperature_unit": "celsius",
                "feels_like": temp_c,  # NWS doesn't provide feels_like in basic forecast
                "precipitation": 0,
                "precipitation_unit": "mm",
                "humidity": current.get("relativeHumidity", {}).get("value", 0) or 0,
                "pressure": 0,  # Not in basic forecast
                "wind_speed": wind_ms,
                "wind_unit": "m/s",
                "conditions": current["shortForecast"],
                "description": f"Current weather in {location}: {current['shortForecast']}, {temp_c}°C, wind {wind_str} {current.get('windDirection', '')}"
            },
            "source": "nws"
        }
    except Exception as e:
        logger.warning(f"NWS API error: {e}")
        return None


def _mock_weather(location: str, timeframe: str) -> dict:
    """
    Fallback mock data when no API is available.
    Returns a properly structured dictionary to prevent crashes.
    """
    return {
        "location": location,
        "timeframe": timeframe,
        "patterns": {
            "average_temperature": 15.0,
            "temperature_unit": "celsius",
            "feels_like": 14.0,
            "precipitation": 0,
            "precipitation_unit": "mm",
            "humidity": 65,
            "pressure": 1013,
            "wind_speed": 3.0,
            "wind_unit": "m/s",
            "conditions": "partly cloudy",
            "description": f"Weather data unavailable for {location}. Using placeholder: partly cloudy, ~15°C."
        },
        "source": "mock",
        "error": "No weather API available - OPENWEATHER_KEY not set and location not in US coverage"
    }