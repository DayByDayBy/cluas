import httpx
from typing import Dict, Optional, Any
from .locations import LOCATION_COORDS

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

def check_local_weather_sync(location: str | None = None, character: Any = None) -> dict:
    """Sync wrapper for MCP executor.
    
    Handles both sync and async contexts safely.
    If called from async context, creates new event loop in thread.
    """
    import asyncio
    import threading
    
    try:
        # Check if we're in an async context
        asyncio.get_running_loop()
        # We're in async context - create new loop in thread
        result_container: Dict[str, Any] = {}
        exception_container: Dict[str, Exception] = {}
        
        def run_in_new_loop():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result_container['result'] = new_loop.run_until_complete(
                    check_local_weather(location=location, character=character)
                )
            except Exception as e:
                exception_container['exception'] = e
            finally:
                new_loop.close()
        
        thread = threading.Thread(target=run_in_new_loop)
        thread.start()
        thread.join()
        
        if 'exception' in exception_container:
            raise exception_container['exception']
        return result_container['result']
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        return asyncio.run(check_local_weather(location=location, character=character))


async def check_local_weather(location: str | None = None, character: Any = None) -> dict:
    """Fetch casual weather description for a location or a character's location."""
    if location is None and character is not None:
        location = getattr(character, "location", None)

    if not location:
        return {
            "location": "unknown",
            "temperature": "N/A",
            "feels_like": "N/A",
            "condition": "unknown",
            "wind_speed": "N/A",
            "precipitation": "N/A",
            "time": "N/A",
        }

    # Parse the string result from check_weather into structured dict
    weather_str = await check_weather(location)
    
    # Extract structured data from the weather string
    # Format: "It's {temp}°C (feels like {apparent}°C); {condition}; {wind}; {precip}; {day/night} in {location}."
    # This is a simplified parser - in production, check_weather should return structured data
    coords = LOCATION_COORDS.get(location, {})
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={coords['lat']}&longitude={coords['lon']}"
            f"&current_weather=true&hourly=temperature_2m,precipitation,weathercode"
        )
        import httpx
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
        
        hourly_precip = data.get("hourly", {}).get("precipitation", [])
        if hourly_precip:
            recent_precip = sum(hourly_precip[-3:])
        else:
            recent_precip = 0
        
        weather_desc = WEATHER_CODE_MAP.get(code, "unknown conditions")
        
        return {
            "location": location,
            "temperature": f"{temp}",
            "feels_like": f"{apparent}",
            "condition": weather_desc,
            "wind_speed": f"{wind}",
            "precipitation": f"{recent_precip} mm" if recent_precip > 0 else "0 mm",
            "time": "day" if is_day else "night",
        }
    except Exception as e:
        return {
            "location": location,
            "temperature": "N/A",
            "feels_like": "N/A",
            "condition": f"Error: {str(e)}",
            "wind_speed": "N/A",
            "precipitation": "N/A",
            "time": "N/A",
        }