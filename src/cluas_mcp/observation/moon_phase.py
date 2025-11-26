from datetime import datetime
from typing import Optional

def fetch_moon_phase(date: Optional[str] = None) -> dict:
    """Get current moon phase (same worldwide)"""
    if date is None:
        date = datetime.now()
    else:
        date = datetime.fromisoformat(date)
    
    # known new moon reference
    known_new_moon = datetime(2000, 1, 6, 18, 14)
    days_since = (date - known_new_moon).days
    lunar_cycle = 29.53058867
    phase = (days_since % lunar_cycle) / lunar_cycle
    
    phase_names = ["New Moon", "Waxing Crescent", "First Quarter", 
                   "Waxing Gibbous", "Full Moon", "Waning Gibbous",
                   "Last Quarter", "Waning Crescent"]
    phase_index = int(phase * 8) % 8
    
    return {
        "phase_name": phase_names[phase_index],
        "illumination": round(phase * 100, 1),
        "date": date.isoformat()
    }