import httpx
from typing import Dict, Optional

# agent locations
LOCATION_COORDS = {
    "Glasgow, Scotland": {"lat": 55.8642, "lon": -4.2518, "country": "UK"},
    "Brooklyn, NY": {"lat": 40.6782, "lon": -73.9442, "country": "US"},
    "Seattle, WA": {"lat": 47.6062, "lon": -122.3321, "country": "US"},
    "Tokyo, Japan": {"lat": 35.6762, "lon": 139.6503, "country": "JP"},
}

# weather codes → casual description
WEATHER_CODE_MAP = {
    0: "sunny and clear",
    1: "mostly sunny",
    2: "partly cloudy",
    3: "cloudy",
    45: "foggy",
    48: "rime fog",
    51: "light drizzle",
    53: "drizzling",
    55: "heavy drizzle",
    61: "light rain",
    63: "raining",
    65: "heavy rain",
    71: "light snow",
    73: "snowing",
    75: "heavy snow",
    80: "rain showers",
    81: "moderate rain showers",
    82: "heavy rain showers",
}

def _precipitation_vibe(precip_mm: float) -> str:
    """Return casual string describing precipitation intensity."""
    if precip_mm == 0:
        return ""
    elif precip_mm < 1:
        return "just a drizzle"
    elif precip_mm < 5:
        return "light rain"
    elif precip_mm < 10:
        return "moderate rain"
    else:
        return "heavy rain"

def _daytime_vibe(is_day: int) -> str:
    """Return a casual day/night description."""
    return "during the day" if is_day else "at night"

async def check_weather(location: str) -> str:
    """Fetch current weather for a location and return a casual description."""
    coords = LOCATION_COORDS.get(location)
    if not coords:
        return f"Sorry, I don’t have weather info for {location}."
    
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={coords['lat']}&longitude={coords['lon']}"
            f"&current_weather=true&hourly=temperature_2m,precipitation,weathercode"
        )
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        current = data.get("current_weather", {})
        temp = current.get("temperature")
        apparent = current.get("apparent_temperature", temp)
        code = current.get("weathercode")
        wind = current.get("windspeed", 0)
        is_day = current.get("is_day", 1)

        # casual precipitation: sum last 3 hours if available
        hourly_precip = data.get("hourly", {}).get("precipitation", [])
        if hourly_precip:
            recent_precip = sum(hourly_precip[-3:])
        else:
            recent_precip = 0
        precip_desc = _precipitation_vibe(recent_precip)

        weather_desc = WEATHER_CODE_MAP.get(code, "unknown conditions")
        day_desc = _daytime_vibe(is_day)

        # optional wind 'vibe'
        wind_desc = "calm wind" if wind < 5 else f"wind {wind} km/h"

        #  casual description
        vibe_parts = [
            f"{temp}°C (feels like {apparent}°C)",
            weather_desc,
            wind_desc,
        ]
        if precip_desc:
            vibe_parts.append(precip_desc)
        vibe_parts.append(day_desc)

        return f"It’s {'; '.join(vibe_parts)} in {location}."
    
    except Exception as e:
        return f"Sorry, I couldn’t fetch the weather for {location} right now. ({e})"

async def check_local_weather(character) -> str:
    """Fetch casual weather description for character's location."""
    location = getattr(character, "location", None)
    if not location:
        return "I don’t know where you are, so I can’t check the weather!"
    return await check_weather(location)
