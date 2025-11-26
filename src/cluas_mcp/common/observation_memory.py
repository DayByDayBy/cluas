import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Optional, Any


class ObservationMemory:
    """
    JSON-backed memory system for storing observational data.
    Supports querying by type, location, date range, and tags.
    Designed for temporal pattern analysis.
    """

    def __init__(self, memory_file: str = "src/data/observations.json"):
        self.memory_file = Path(memory_file)
        if not self.memory_file.exists():
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_memory({})
        self.memory = self._read_memory()

    # --- Internal file operations ---
    def _read_memory(self) -> Dict:
        with open(self.memory_file, "r") as f:
            return json.load(f)

    def _write_memory(self, data: Dict):
        with open(self.memory_file, "w") as f:
            json.dump(data, f, indent=2)

    # --- Memory operations ---
    def add_observation(
        self,
        obs_type: str,
        location: str,
        data: Dict[str, Any],
        conditions: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        notes: str = ""
    ) -> str:
        """
        Add a new observation to memory.
        
        Args:
            obs_type: Type of observation (bird_sighting, weather, air_quality, moon_phase, sun_times)
            location: Location of observation
            data: The actual observation data (tool result)
            conditions: Environmental context (weather, moon, air quality, etc.)
            tags: List of tags for categorization
            notes: Optional notes about the observation
            
        Returns:
            observation_id: Unique ID of the stored observation
        """
        now = datetime.now(UTC).isoformat()
        obs_id = f"obs_{uuid.uuid4().hex[:8]}"
        
        self.memory[obs_id] = {
            "id": obs_id,
            "timestamp": now,
            "type": obs_type,
            "location": location,
            "data": data,
            "conditions": conditions or {},
            "tags": tags or [],
            "notes": notes
        }
        
        self._write_memory(self.memory)
        return obs_id

    def get_by_type(self, obs_type: str) -> List[Dict]:
        """Return all observations of a specific type."""
        return [
            obs for obs in self.memory.values()
            if obs.get("type") == obs_type
        ]

    def get_by_location(self, location: str) -> List[Dict]:
        """Return all observations from a specific location (case-insensitive)."""
        location_lower = location.lower()
        return [
            obs for obs in self.memory.values()
            if location_lower in obs.get("location", "").lower()
        ]

    def get_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Return observations within a date range.
        
        Args:
            start_date: Start of range (inclusive). If None, no lower bound.
            end_date: End of range (inclusive). If None, no upper bound.
        """
        results = []
        for obs in self.memory.values():
            obs_time = datetime.fromisoformat(obs["timestamp"])
            
            if start_date and obs_time < start_date:
                continue
            if end_date and obs_time > end_date:
                continue
                
            results.append(obs)
        
        return sorted(results, key=lambda x: x["timestamp"])

    def get_recent(self, days: int = 7) -> List[Dict]:
        """Return observations from the last N days."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return self.get_by_date_range(start_date=cutoff)

    def get_by_tag(self, tag: str) -> List[Dict]:
        """Return observations with a specific tag."""
        return [
            obs for obs in self.memory.values()
            if tag in obs.get("tags", [])
        ]

    def search_observations(
        self,
        obs_type: Optional[str] = None,
        location: Optional[str] = None,
        tags: Optional[List[str]] = None,
        days: Optional[int] = None
    ) -> List[Dict]:
        """
        Flexible search combining multiple criteria.
        
        Args:
            obs_type: Filter by observation type
            location: Filter by location (partial match)
            tags: Filter by tags (must have ALL tags)
            days: Only include observations from last N days
        """
        results = list(self.memory.values())
        
        if obs_type:
            results = [obs for obs in results if obs.get("type") == obs_type]
        
        if location:
            location_lower = location.lower()
            results = [
                obs for obs in results
                if location_lower in obs.get("location", "").lower()
            ]
        
        if tags:
            results = [
                obs for obs in results
                if all(tag in obs.get("tags", []) for tag in tags)
            ]
        
        if days:
            cutoff = datetime.now(UTC) - timedelta(days=days)
            results = [
                obs for obs in results
                if datetime.fromisoformat(obs["timestamp"]) >= cutoff
            ]
        
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def analyze_patterns(
        self,
        obs_type: str,
        location: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze patterns in observations for temporal analysis.
        
        Args:
            obs_type: Type of observation to analyze
            location: Optional location filter
            days: Number of days to analyze
            
        Returns:
            Dictionary with pattern analysis (count, frequency, trends)
        """
        observations = self.search_observations(
            obs_type=obs_type,
            location=location,
            days=days
        )
        
        if not observations:
            return {
                "type": obs_type,
                "location": location,
                "days": days,
                "count": 0,
                "message": "No observations found for analysis"
            }
        
        # Group by date
        by_date = {}
        for obs in observations:
            date = obs["timestamp"][:10]  # YYYY-MM-DD
            by_date[date] = by_date.get(date, 0) + 1
        
        # Calculate frequency
        total_days = len(by_date)
        avg_per_day = len(observations) / max(total_days, 1)
        
        return {
            "type": obs_type,
            "location": location,
            "days": days,
            "count": len(observations),
            "total_days_with_observations": total_days,
            "average_per_day": round(avg_per_day, 2),
            "date_distribution": by_date,
            "earliest": observations[-1]["timestamp"] if observations else None,
            "latest": observations[0]["timestamp"] if observations else None
        }

    def get_conditions_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get a summary of environmental conditions from recent observations.
        Useful for understanding context.
        """
        recent = self.get_recent(days=days)
        
        conditions_data = {
            "moon_phases": [],
            "weather_conditions": [],
            "air_quality_readings": [],
            "temperatures": []
        }
        
        for obs in recent:
            cond = obs.get("conditions", {})
            
            if "moon_phase" in cond:
                conditions_data["moon_phases"].append(cond["moon_phase"])
            
            if "weather" in cond:
                conditions_data["weather_conditions"].append(cond["weather"])
            
            if "air_quality" in cond:
                conditions_data["air_quality_readings"].append(cond["air_quality"])
            
            if "temperature" in cond:
                conditions_data["temperatures"].append(cond["temperature"])
        
        return {
            "days": days,
            "observation_count": len(recent),
            "conditions": conditions_data
        }

    def all_observations(self) -> List[Dict]:
        """Return all observations sorted by timestamp (newest first)."""
        return sorted(
            self.memory.values(),
            key=lambda x: x["timestamp"],
            reverse=True
        )

    def delete_observation(self, obs_id: str) -> bool:
        """Delete a specific observation by ID."""
        if obs_id in self.memory:
            del self.memory[obs_id]
            self._write_memory(self.memory)
            return True
        return False

    def prune_old(self, older_than_days: int = 365):
        """Remove observations older than specified days."""
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        
        ids_to_delete = [
            obs_id for obs_id, obs in self.memory.items()
            if datetime.fromisoformat(obs["timestamp"]) < cutoff
        ]
        
        for obs_id in ids_to_delete:
            del self.memory[obs_id]
        
        if ids_to_delete:
            self._write_memory(self.memory)
        
        return len(ids_to_delete)

    def clear_all(self):
        """Clear all observations (use with caution!)."""
        self.memory = {}
        self._write_memory({})


# Usage example:
# from src.cluas_mcp.common.observation_memory import ObservationMemory
#
# memory = ObservationMemory()
#
# # Add a bird sighting observation
# memory.add_observation(
#     obs_type="bird_sighting",
#     location="Tokyo, Japan",
#     data={"species": "Jungle Crow", "count": 3},
#     conditions={
#         "moon_phase": "Full Moon",
#         "weather": "Clear",
#         "temperature": 18.5,
#         "air_quality": 45
#     },
#     tags=["morning", "behavioral"],
#     notes="Observed near park at dawn"
# )
#
# # Analyze patterns
# patterns = memory.analyze_patterns("bird_sighting", location="Tokyo", days=30)
# print(patterns)
#
# # Get recent observations
# recent = memory.get_recent(days=7)