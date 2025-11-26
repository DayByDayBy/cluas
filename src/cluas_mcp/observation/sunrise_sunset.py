from astral import LocationInfo
from astral.sun import sun
from datetime import datetime, date

LOCATIONS = {
    "brooklyn": LocationInfo("Brooklyn", "USA", "America/New_York", 40.6782, -73.9442),
    "glasgow": LocationInfo("Glasgow", "Scotland", "Europe/London", 55.8642, -4.2518),
    "tokyo": LocationInfo("Tokyo", "Japan", "Asia/Tokyo", 35.6762, 139.6503),
    "seattle": LocationInfo("Seattle", "USA", "America/Los_Angeles", 47.6062, -122.3321)
}

def fetch_sunrise_sunset(location: str, date_str: Optional[str] = None) -> dict:
    """Get sunrise/sunset times for specific cities"""
    location = location.lower()
    if location not in LOCATIONS:
        return {"error": f"Location must be one of: {list(LOCATIONS.keys())}"}
    
    loc = LOCATIONS[location]
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    
    s = sun(loc.observer, date=target_date, tzinfo=loc.timezone)
    
    return {
        "location": location.title(),
        "date": target_date.isoformat(),
        "sunrise": s['sunrise'].strftime('%H:%M'),
        "sunset": s['sunset'].strftime('%H:%M'),
        "timezone": str(loc.timezone)
    }