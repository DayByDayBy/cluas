import requests

# Agent locations
LOCATION_COORDS = {
    "Glasgow, Scotland": {"lat": 55.8642, "lon": -4.2518, "country": "UK"},
    "Brooklyn, NY": {"lat": 40.6782, "lon": -73.9442, "country": "US"},
    "Seattle, WA": {"lat": 47.6062, "lon": -122.3321, "country": "US"},
    "Tokyo, Japan": {"lat": 35.6762, "lon": 139.6503, "country": "JP"},
}

# Weather codes → casual description
WEATHER_CODE_MAP = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    73: "moderate snow",
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
        return "drizzling"
    elif precip_mm < 5:
        return "light rain"
    elif precip_mm < 10:
        return "moderate rain"
    else:
        return "heavy rain"

def check_weather(location: str) -> str:
    coords = LOCATION_COORDS.get(location)
    if not coords:
        return f"Weather info unavailable for {location}"

    try:
        # Fetch current weather + precipitation for casual vibe
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={coords['lat']}&longitude={coords['lon']}"
            f"&current_weather=true&hourly=precipitation"
        )
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        current = data.get("current_weather", {})
        temp = current.get("temperature")
        apparent = current.get("apparent_temperature", temp)
        code = current.get("weathercode")
        wind = current.get("windspeed", 0)
        is_day = current.get("is_day", 1)

        # Optional: take latest hourly precipitation if available
        hourly_precip = data.get("hourly", {}).get("precipitation", [])
        precip_mm = hourly_precip[-1] if hourly_precip else 0
        precip_desc = _precipitation_vibe(precip_mm)

        weather_desc = WEATHER_CODE_MAP.get(code, "unknown conditions")
        day_desc = "daytime" if is_day else "night"

        # Build casual description
        vibe_parts = [
            f"{temp}°C (feels like {apparent}°C)",
            weather_desc,
            f"wind {wind} km/h",
        ]
        if precip_desc:
            vibe_parts.append(precip_desc)
        vibe_parts.append(day_desc)

        return "It's " + ", ".join(vibe_parts) + f" in {location}"

    except Exception as e:
        return f"Weather info unavailable for {location} ({e})"

def check_local_weather(character) -> str:
    """Fetch casual weather description for character's location."""
    return check_weather(character.location)
