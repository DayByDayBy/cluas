"""a bunch of formatters for server.py"""


__all__ = [
    'format_bird_sightings',
    'format_news_results',
    'format_local_weather',
    'format_search_results',
    'format_temporal_patterns',
    'format_trend_angles',
    'format_trending_topics',
    'format_weather_patterns',
    'format_web_search_results'
]


def format_search_results(results: dict) -> str:
    """format search results into readable string"""
    output = []
    
    pubmed_results = results.get("pubmed", [])
    if pubmed_results:
        output.append("=== PubMed Results ===\n")
        for i, paper in enumerate(pubmed_results[:5], 1):
            output.append(f"{i}. {paper.get('title', 'No Title')}\n")
            authors = paper.get('authors', [])
            if authors:
                output.append(f"   Authors: {', '.join(authors[:3])}")
            abstract = paper.get('abstract', 'No Abstract')
            if abstract and abstract != 'No Abstract' and isinstance(abstract, str):
                output.append(f"   Abstract: {abstract[:200]}...\n")
            output.append("")
            
    ss_results = results.get("semantic_scholar", [])
    if ss_results:
        output.append("=== Semantic Scholar Results ===\n")
        for i, paper in enumerate(ss_results[:5], 1):
            output.append(f"{i}. {paper.get('title', 'No Title')}\n")
            authors = paper.get('authors', [])
            if authors:
                output.append(f"   Authors: {', '.join(authors[:3])}")
            abstract = paper.get('abstract', 'No Abstract')
            if abstract != 'No Abstract':
                output.append(f"   Abstract: {abstract[:200]}...\n")
            output.append("")
            
    arxiv_results = results.get("arxiv", [])
    if arxiv_results:
        output.append("=== ArXiv Results ===\n")
        for i, paper in enumerate(arxiv_results[:5], 1):
            output.append(f"{i}. {paper.get('title', 'No Title')}\n")
            authors = paper.get('authors', [])
            if authors:
                output.append(f"   Authors: {', '.join(authors[:3])}")
            abstract = paper.get('abstract', 'No Abstract')
            if abstract != 'No Abstract':
                output.append(f"   Abstract: {abstract[:200]}...\n")
            output.append("")
    
    if not output:
        return "No results found."
    
    return "\n".join(output)

def format_web_search_results(results: dict) -> str:
    """Format web search results into readable string"""
    output = []
    output.append(f"=== Web Search Results for: {results.get('query', 'N/A')} ===\n")
    
    search_results = results.get("results", [])
    if search_results:
        for i, result in enumerate(search_results, 1):
            output.append(f"{i}. {result.get('title', 'No Title')}\n")
            output.append(f"   URL: {result.get('url', 'N/A')}\n")
            output.append(f"   {result.get('snippet', 'No snippet')}\n")
            output.append("")
    else:
        output.append("No results found.\n")
    
    return "\n".join(output)

def format_trending_topics(results: dict) -> str:
    """Format trending topics into readable string"""
    output = []
    output.append(f"=== Trending Topics ({results.get('category', 'general')}) ===\n")
    
    topics = results.get("trending_topics", [])
    if topics:
        for i, topic in enumerate(topics, 1):
            output.append(f"{i}. {topic.get('topic', 'N/A')} (Score: {topic.get('trend_score', 0)})\n")
            output.append(f"   {topic.get('description', 'No description')}\n")
            output.append("")
    else:
        output.append("No trending topics found.\n")
    
    return "\n".join(output)

def format_trend_angles(results: dict) -> str:
    """Format trend angles analysis into readable string"""
    output = []
    output.append("=== Trend Analysis: Multiple Angles ===\n")
    
    # Trending status
    trending = results.get("trending", {})
    if trending:
        output.append("📈 **TRENDING STATUS**")
        topics = trending.get("trending_topics", [])
        if topics:
            for i, topic in enumerate(topics[:3], 1):
                output.append(f"{i}. {topic.get('topic', 'N/A')} (Score: {topic.get('trend_score', 0)})")
        else:
            output.append("No specific trending data found")
        output.append(f"Source: {trending.get('source', 'N/A')}\n")
    
    # Surface drivers
    drivers = results.get("surface_drivers", {})
    if drivers:
        output.append("🔍 **WHY IT'S TRENDING**")
        search_results = drivers.get("results", [])
        if search_results:
            for i, result in enumerate(search_results[:3], 1):
                output.append(f"{i}. {result.get('title', 'N/A')}")
                output.append(f"   {result.get('snippet', 'No snippet')}\n")
        else:
            output.append("No driver analysis available\n")
    
    # Cultural narrative
    narrative = results.get("narrative", {})
    if narrative:
        output.append("🌍 **CULTURAL NARRATIVE**")
        search_results = narrative.get("results", [])
        if search_results:
            for i, result in enumerate(search_results[:3], 1):
                output.append(f"{i}. {result.get('title', 'N/A')}")
                output.append(f"   {result.get('snippet', 'No snippet')}\n")
        else:
            output.append("No cultural analysis available\n")
    
    # Local angle
    local_angle = results.get("local_angle", {})
    if local_angle:
        output.append("📍 **LOCAL CONTEXT**")
        search_results = local_angle.get("results", [])
        if search_results:
            for i, result in enumerate(search_results[:3], 1):
                output.append(f"{i}. {result.get('title', 'N/A')}")
                output.append(f"   {result.get('snippet', 'No snippet')}\n")
        else:
            output.append("No local analysis available\n")
    
    # Criticism
    criticism = results.get("criticism", {})
    if criticism:
        output.append("⚠️ **CRITICISM & PROBLEMS**")
        search_results = criticism.get("results", [])
        if search_results:
            for i, result in enumerate(search_results[:3], 1):
                output.append(f"{i}. {result.get('title', 'N/A')}")
                output.append(f"   {result.get('snippet', 'No snippet')}\n")
        else:
            output.append("No critical analysis available\n")
    
    if not any([trending, drivers, narrative, local_angle, criticism]):
        output.append("No trend analysis data available. All analysis components failed.")
    
    return "\n".join(output)

def format_local_weather(results: dict) -> str:
    """Format local weather data into readable string"""
    return (
        f"=== Local Weather: {results.get('location', 'N/A')} ===\n"
        f"Temperature: {results.get('temperature', 'N/A')}°C\n"
        f"Feels like: {results.get('feels_like', 'N/A')}°C\n"
        f"Conditions: {results.get('condition', 'N/A')}\n"
        f"Wind: {results.get('wind_speed', 'N/A')} km/h\n"
        f"Precipitation: {results.get('precipitation', 'N/A')}\n"
        f"Time: {results.get('time', 'N/A')}\n"
    )

def format_news_results(results: dict) -> str:
    """Format news search results into readable string"""
    output = []
    output.append(f"=== News Search Results for: {results.get('query', 'N/A')} ===\n")
    
    articles = results.get("articles", [])
    if articles:
        for i, article in enumerate(articles, 1):
            output.append(f"{i}. {article.get('title', 'No Title')}\n")
            output.append(f"   Source: {article.get('source', 'Unknown')}\n")
            output.append(f"   Published: {article.get('published_date', 'Unknown')}\n")
            output.append(f"   {article.get('summary', 'No summary')}\n")
            output.append(f"   URL: {article.get('url', 'N/A')}\n")
            output.append("")
    else:
        output.append("No news articles found.\n")
    
    return "\n".join(output)


def format_bird_sightings(results: dict) -> str:
    """Format bird sightings into readable string"""
    output = []
    output.append(f"=== Bird Sightings: {results.get('species', 'all')} in {results.get('location', 'N/A')} ===\n")
    
    sightings = results.get("sightings", [])
    if sightings:
        for i, sighting in enumerate(sightings, 1):
            output.append(f"{i}. {sighting.get('common_name', 'Unknown')} ({sighting.get('species', 'Unknown')})\n")
            output.append(f"   Date: {sighting.get('date', 'Unknown')}\n")
            output.append(f"   Location: {sighting.get('location', 'Unknown')}\n")
            output.append(f"   Notes: {sighting.get('notes', 'No notes')}\n")
            output.append("")
    else:
        output.append("No sightings found.\n")
    
    output.append(f"Total Sightings: {results.get('total_sightings', 0)}\n")
    
    return "\n".join(output)

def format_weather_patterns(results: dict) -> str:
    """Format weather patterns into readable string"""
    output = []
    patterns = results.get("patterns", {})
    output.append(f"=== Weather Patterns: {results.get('location', 'N/A')} ({results.get('timeframe', 'N/A')}) ===\n")
    output.append(f"Average Temperature: {patterns.get('average_temperature', 'N/A')} {patterns.get('temperature_unit', '')}\n")
    output.append(f"Precipitation: {patterns.get('precipitation', 'N/A')} {patterns.get('precipitation_unit', '')}\n")
    output.append(f"Humidity: {patterns.get('humidity', 'N/A')}%\n")
    output.append(f"Wind Speed: {patterns.get('wind_speed', 'N/A')} {patterns.get('wind_unit', '')}\n")
    output.append(f"Description: {patterns.get('description', 'No description')}\n")
    
    return "\n".join(output)

def format_temporal_patterns(results: dict) -> str:
    """Format temporal pattern analysis into readable string"""
    output = []
    
    # Header
    output.append(f"=== Temporal Pattern Analysis: {results.get('data_type', 'N/A')} in {results.get('location', 'N/A')} ===\n")
    
    # Basic info
    output.append(f"Analysis Period: {results.get('days', 'N/A')} days")
    output.append(f"Total Observations: {results.get('observation_count', 'N/A')}")
    
    time_range = results.get('time_range', {})
    if time_range:
        output.append(f"Time Range: {time_range.get('start', 'N/A')} to {time_range.get('end', 'N/A')}")
    
    output.append(f"Source: {results.get('source', 'N/A')}\n")
    
    # Analysis results
    analysis = results.get("analysis", {})
    
    if analysis.get("status") == "no_data":
        output.append(f"Status: No Data Available")
        output.append(f"Message: {analysis.get('message', 'No observations found')}\n")
        return "\n".join(output)
    
    # Basic statistics
    basic_stats = analysis.get("basic_stats", {})
    if basic_stats:
        output.append("=== Basic Statistics ===")
        output.append(f"Total Observations: {basic_stats.get('total_observations', 'N/A')}")
        output.append(f"Unique Days with Data: {basic_stats.get('unique_days', 'N/A')}")
        output.append(f"Average per Day: {basic_stats.get('average_per_day', 'N/A')}")
        output.append(f"Maximum per Day: {basic_stats.get('max_per_day', 'N/A')}")
        output.append(f"Minimum per Day: {basic_stats.get('min_per_day', 'N/A')}")
        output.append(f"Daily Standard Deviation: {basic_stats.get('daily_std_dev', 'N/A')}\n")
    
    # Temporal patterns
    temporal_patterns = analysis.get("temporal_patterns", {})
    if temporal_patterns:
        output.append("=== Temporal Patterns ===")
        
        # Trend analysis
        trend = temporal_patterns.get("trend", {})
        if trend:
            output.append(f"Trend: {trend.get('direction', 'N/A').title()}")
            output.append(f"Trend Slope: {trend.get('slope', 'N/A')}")
            output.append(f"Trend Confidence: {trend.get('confidence', 'N/A')}\n")
        
        # Seasonality
        seasonality = temporal_patterns.get("seasonality", {})
        if seasonality:
            output.append(f"Seasonality Level: {seasonality.get('level', 'N/A').title()}")
            output.append(f"Seasonality Strength: {seasonality.get('strength', 'N/A')}")
            
            monthly_dist = seasonality.get("monthly_distribution", {})
            if monthly_dist:
                output.append("Monthly Distribution:")
                for month, count in sorted(monthly_dist.items()):
                    output.append(f"  {month}: {count}")
            output.append("")
        
        # Peak periods
        peak_periods = temporal_patterns.get("peak_periods", {})
        if peak_periods:
            output.append("=== Peak Activity Periods ===")
            output.append(f"Peak Hour of Day: {peak_periods.get('hour_of_day', 'N/A')}:00")
            output.append(f"Peak Day of Week: {peak_periods.get('day_of_week', 'N/A')}")
            
            top_dates = peak_periods.get("top_dates", [])
            if top_dates:
                output.append("Top 3 Most Active Dates:")
                for date, count in top_dates:
                    output.append(f"  {date}: {count} observations")
            output.append("")
        
        # Distribution by hour and weekday
        distribution = temporal_patterns.get("distribution", {})
        if distribution:
            output.append("=== Activity Distribution ===")
            
            hourly_dist = distribution.get("by_hour", {})
            if hourly_dist:
                output.append("By Hour of Day:")
                for hour in sorted(hourly_dist.keys()):
                    bar = "█" * min(20, hourly_dist[hour])  # Simple bar chart
                    output.append(f"  {hour:02d}:00 {hourly_dist[hour]:2d} {bar}")
            
            weekday_dist = distribution.get("by_weekday", {})
            if weekday_dist:
                output.append("\nBy Day of Week:")
                for day, count in weekday_dist.items():
                    bar = "█" * min(20, count)
                    output.append(f"  {day:10s} {count:2d} {bar}")
            output.append("")
    
    # Environmental correlations
    env_corr = results.get("environmental_correlations", {})
    if env_corr and env_corr.get("correlations"):
        output.append("=== Environmental Correlations ===")
        output.append(f"Available Conditions: {', '.join(env_corr.get('available_conditions', []))}")
        output.append(f"Sample Size: {env_corr.get('sample_size', 'N/A')} observations\n")
        
        correlations = env_corr.get("correlations", {})
        for condition, data in correlations.items():
            output.append(f"{condition.title()}:")
            if data.get("type") == "categorical":
                output.append(f"  Type: Categorical")
                output.append(f"  Most Common: {data.get('most_common', 'N/A')}")
                dist = data.get("distribution", {})
                for value, count in sorted(dist.items(), key=lambda x: x[1], reverse=True)[:5]:
                    output.append(f"    {value}: {count}")
            elif data.get("type") == "numerical":
                output.append(f"  Type: Numerical")
                output.append(f"  Mean: {data.get('mean', 'N/A')}")
                output.append(f"  Median: {data.get('median', 'N/A')}")
                output.append(f"  Range: {data.get('min', 'N/A')} - {data.get('max', 'N/A')}")
                output.append(f"  Std Dev: {data.get('std_dev', 'N/A')}")
            output.append("")
    
    # Predictions
    predictions = results.get("predictions", {})
    if predictions:
        output.append("=== Predictions ===")
        if predictions.get("status") == "success":
            next_day = predictions.get("next_day_prediction", {})
            if next_day:
                output.append(f"Expected Observations Tomorrow: {next_day.get('expected_observations', 'N/A')}")
                output.append(f"Prediction Confidence: {next_day.get('confidence', 'N/A')}")
            
            optimal_times = predictions.get("optimal_observation_times", [])
            if optimal_times:
                output.append(f"Optimal Observation Times: {', '.join(optimal_times)}")
            
            output.append(f"Based on: {predictions.get('based_on_days', 'N/A')} recent days")
        else:
            output.append(f"Prediction Status: {predictions.get('status', 'N/A')}")
            output.append(f"Message: {predictions.get('message', 'No prediction available')}")
        output.append("")
    
    return "\n".join(output)