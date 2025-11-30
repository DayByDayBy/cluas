import logging
from typing import Optional
from src.cluas_mcp.observation.ebird import fetch_bird_sightings, format_sightings_for_display
from src.cluas_mcp.observation.weather import fetch_weather_patterns
from src.cluas_mcp.observation.airquality import fetch_air_quality
from src.cluas_mcp.observation.moon_phase import fetch_moon_phase
from src.cluas_mcp.observation.sunrise_sunset import fetch_sunrise_sunset
from src.cluas_mcp.common.observation_memory import ObservationMemory

logger = logging.getLogger(__name__)

def get_bird_sightings(location: str = "HuggingFace HQ, Brooklyn, NY", species: Optional[str] = None) -> dict:
    """
    Get recent bird sightings near a location.
    
    Args:
        location: Location to search (defaults to HF HQ)
        species: Optional species filter (e.g., 'corvus')
    
    Returns:
        Dictionary with sightings data
    """
    logger.info(f"Bird sightings tool called for: {location} with species: {species}")
    
    sightings = fetch_bird_sightings(location=location, species=species)
    
    formatted = []
    for s in sightings:
        formatted.append({
            "common_name": s.get("comName", "Unknown"),
            "species": s.get("sciName", "Unknown"),
            "date": s.get("obsDt", "Unknown"),
            "location": s.get("locName", "Unknown"),
            "count": s.get("howMany", 1)
        })
    
    return {
        "location": location,
        "species_filter": species,
        "sightings": formatted,
        "total_sightings": len(formatted)
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

def analyze_temporal_patterns(data_type: str, location: str = "global", days: int = 30) -> dict:
    """
    Analyze temporal patterns from stored observations with comprehensive statistical analysis.
    
    Args:
        data_type: Type of data to analyze (e.g., "bird_sightings", "weather", "behavior")
        location: Location to analyze patterns for
        days: Number of days to analyze (default: 30)
        
    Returns:
        Dictionary with comprehensive temporal pattern analysis including:
        - Basic statistics (count, frequency, distribution)
        - Trend analysis (increasing/decreasing/stable)
        - Seasonality detection
        - Peak activity periods
        - Correlations with environmental conditions
        - Predictive insights
    """
    logger.info("Analyzing temporal patterns for data_type: %s, location: %s, days: %d", data_type, location, days)
    
    memory = ObservationMemory(location=location)
    observations = memory.search_observations(
        obs_type=data_type,
        location=location if location != "global" else None,
        days=days
    )
    
    if not observations:
        return {
            "data_type": data_type,
            "location": location,
            "days": days,
            "analysis": {
                "status": "no_data",
                "message": f"No observations found for {data_type} in {location} over the last {days} days"
            },
            "source": "observation_memory"
        }
    
    # Perform comprehensive analysis
    analysis = _perform_comprehensive_analysis(observations, data_type)
    
    # Get environmental correlations if conditions data available
    environmental_analysis = _analyze_environmental_correlations(observations)
    
    # Generate predictions based on patterns
    predictions = _generate_predictions(observations, analysis)
    
    return {
        "data_type": data_type,
        "location": location,
        "days": days,
        "observation_count": len(observations),
        "time_range": {
            "start": observations[-1]["timestamp"],
            "end": observations[0]["timestamp"]
        },
        "analysis": analysis,
        "environmental_correlations": environmental_analysis,
        "predictions": predictions,
        "source": "observation_memory"
    }


def _perform_comprehensive_analysis(observations: list, data_type: str) -> dict:
    """Perform comprehensive statistical analysis on observations."""
    from datetime import datetime, timedelta
    import statistics
    
    # Time-based analysis
    timestamps = [datetime.fromisoformat(obs["timestamp"]) for obs in observations]
    dates = [ts.date() for ts in timestamps]
    hours = [ts.hour for ts in timestamps]
    weekdays = [ts.weekday() for ts in timestamps]  # 0=Monday, 6=Sunday
    
    # Group by different time periods
    daily_counts = {}
    hourly_counts = {}
    weekly_counts = {}
    
    for i, obs in enumerate(observations):
        date = dates[i].isoformat()
        hour = hours[i]
        weekday = weekdays[i]
        
        daily_counts[date] = daily_counts.get(date, 0) + 1
        hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        weekly_counts[weekday] = weekly_counts.get(weekday, 0) + 1
    
    # Calculate trend (simple linear regression on daily counts)
    trend_analysis = _calculate_trend(daily_counts)
    
    # Find peak periods
    peak_hour = max(hourly_counts, key=hourly_counts.get)
    peak_weekday = max(weekly_counts, key=weekly_counts.get)
    peak_dates = sorted(daily_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Calculate frequency statistics
    total_days = len(daily_counts)
    avg_per_day = len(observations) / max(total_days, 1)
    daily_values = list(daily_counts.values())
    
    # Detect seasonality patterns
    seasonality = _detect_seasonality(observations)
    
    return {
        "status": "success",
        "basic_stats": {
            "total_observations": len(observations),
            "unique_days": total_days,
            "average_per_day": round(avg_per_day, 2),
            "max_per_day": max(daily_values) if daily_values else 0,
            "min_per_day": min(daily_values) if daily_values else 0,
            "daily_std_dev": round(statistics.stdev(daily_values), 2) if len(daily_values) > 1 else 0
        },
        "temporal_patterns": {
            "trend": trend_analysis,
            "seasonality": seasonality,
            "peak_periods": {
                "hour_of_day": peak_hour,
                "day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][peak_weekday],
                "top_dates": peak_dates
            },
            "distribution": {
                "by_hour": dict(sorted(hourly_counts.items())),
                "by_weekday": {"Monday": weekly_counts.get(0, 0), "Tuesday": weekly_counts.get(1, 0), 
                              "Wednesday": weekly_counts.get(2, 0), "Thursday": weekly_counts.get(3, 0),
                              "Friday": weekly_counts.get(4, 0), "Saturday": weekly_counts.get(5, 0), 
                              "Sunday": weekly_counts.get(6, 0)}
            }
        }
    }


def _calculate_trend(daily_counts: dict) -> dict:
    """Calculate trend using simple linear regression."""
    if len(daily_counts) < 3:
        return {"direction": "insufficient_data", "slope": 0, "confidence": 0}
    
    dates = sorted(daily_counts.keys())
    values = [daily_counts[date] for date in dates]
    
    # Simple linear regression
    n = len(values)
    x = list(range(n))
    sum_x = sum(x)
    sum_y = sum(values)
    sum_xy = sum(x[i] * values[i] for i in range(n))
    sum_x2 = sum(x[i] ** 2 for i in range(n))
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
    
    # Determine trend direction
    if abs(slope) < 0.01:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"
    
    # Simple confidence based on data consistency
    confidence = min(1.0, len(values) / 30.0)  # More confidence with more data points
    
    return {
        "direction": direction,
        "slope": round(slope, 4),
        "confidence": round(confidence, 2)
    }


def _detect_seasonality(observations: list) -> dict:
    """Detect seasonal patterns in observations."""
    from datetime import datetime
    import statistics
    
    # Group by month and week patterns
    monthly_patterns = {}
    weekly_patterns = {}
    
    for obs in observations:
        dt = datetime.fromisoformat(obs["timestamp"])
        month = dt.strftime("%B")
        week_of_year = dt.isocalendar()[1]
        
        monthly_patterns[month] = monthly_patterns.get(month, 0) + 1
        weekly_patterns[week_of_year] = weekly_patterns.get(week_of_year, 0) + 1
    
    # Calculate seasonality strength
    if len(monthly_patterns) > 1:
        monthly_values = list(monthly_patterns.values())
        monthly_std = statistics.stdev(monthly_values) if len(monthly_values) > 1 else 0
        monthly_mean = statistics.mean(monthly_values)
        seasonality_strength = monthly_std / monthly_mean if monthly_mean > 0 else 0
    else:
        seasonality_strength = 0
    
    # Determine seasonality level
    if seasonality_strength < 0.2:
        level = "low"
    elif seasonality_strength < 0.5:
        level = "moderate"
    else:
        level = "high"
    
    return {
        "level": level,
        "strength": round(seasonality_strength, 3),
        "monthly_distribution": monthly_patterns,
        "weekly_distribution": dict(sorted(weekly_patterns.items())[:10])  # Show first 10 weeks
    }


def _analyze_environmental_correlations(observations: list) -> dict:
    """Analyze correlations with environmental conditions."""
    correlations = {}
    condition_data = {}
    
    # Collect condition data
    for obs in observations:
        conditions = obs.get("conditions", {})
        for key, value in conditions.items():
            if key not in condition_data:
                condition_data[key] = []
            condition_data[key].append(value)
    
    # Analyze each condition type
    for condition, values in condition_data.items():
        if len(values) > 1:
            # Simple frequency analysis for categorical data
            if isinstance(values[0], str):
                freq = {}
                for val in values:
                    freq[val] = freq.get(val, 0) + 1
                correlations[condition] = {
                    "type": "categorical",
                    "distribution": freq,
                    "most_common": max(freq, key=freq.get)
                }
            # Statistical analysis for numerical data
            elif isinstance(values[0], (int, float)):
                import statistics
                correlations[condition] = {
                    "type": "numerical",
                    "mean": round(statistics.mean(values), 2),
                    "median": round(statistics.median(values), 2),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": round(statistics.stdev(values), 2) if len(values) > 1 else 0
                }
    
    return {
        "available_conditions": list(condition_data.keys()),
        "correlations": correlations,
        "sample_size": len(observations)
    }


def _generate_predictions(observations: list, analysis: dict) -> dict:
    """Generate simple predictions based on observed patterns."""
    import statistics
    from datetime import datetime, timedelta
    
    if len(observations) < 5:
        return {"status": "insufficient_data", "message": "Need more observations for predictions"}
    
    # Predict next day's activity based on recent patterns
    recent_observations = observations[:7]  # Last 7 days
    recent_daily_counts = {}
    
    for obs in recent_observations:
        date = datetime.fromisoformat(obs["timestamp"]).date().isoformat()
        recent_daily_counts[date] = recent_daily_counts.get(date, 0) + 1
    
    if recent_daily_counts:
        recent_avg = statistics.mean(recent_daily_counts.values())
        trend = analysis["temporal_patterns"]["trend"]["direction"]
        
        # Adjust prediction based on trend
        if trend == "increasing":
            predicted_next_day = recent_avg * 1.1
        elif trend == "decreasing":
            predicted_next_day = recent_avg * 0.9
        else:
            predicted_next_day = recent_avg
        
        # Predict best time for next observation
        hourly_dist = analysis["temporal_patterns"]["peak_periods"]["hour_of_day"]
        best_hour = analysis["temporal_patterns"]["distribution"]["by_hour"]
        peak_hours = sorted(best_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "status": "success",
            "next_day_prediction": {
                "expected_observations": round(predicted_next_day, 1),
                "confidence": analysis["temporal_patterns"]["trend"]["confidence"]
            },
            "optimal_observation_times": [f"{hour}:00" for hour, count in peak_hours],
            "based_on_days": len(recent_daily_counts)
        }
    
    return {"status": "no_recent_data", "message": "No recent data available for prediction"}

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




