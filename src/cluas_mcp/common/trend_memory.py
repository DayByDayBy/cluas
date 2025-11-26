import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Optional, Any


class TrendMemory:
    """
    JSON-backed memory system for storing web search and trending topic data.
    Supports querying by type, location, date range, and tags.
    Designed for tracking search history and trend patterns.
    """

    def __init__(
        self, 
        location: Optional[str] = None, 
        memory_file: Optional[Path] = None):
        """
        Initialize TrendMemory with optional default location.
        Args:
            location: Default location context for entries (e.g., "Brooklyn")
        """
        self.default_location = location
        self.memory_file = Path(memory_file) if memory_file else Path.home() / ".cluas_mcp" / "trend_memory.json"

        self._ensure_data_dir()
        if not self.memory_file.exists():
            self._write_memory({})
        self.memory = self._read_memory()

    # --- Internal file operations ---
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

    def _read_memory(self) -> Dict:
        with open(self.memory_file, "r") as f:
            return json.load(f)

    def _write_memory(self, data: Dict):
        with open(self.memory_file, "w") as f:
            json.dump(data, f, indent=2)

    # --- Memory operations ---
    def add_search(
        self,
        query: str,
        results: Dict[str, Any],
        search_type: str = "web_search",
        tags: Optional[List[str]] = None,
        notes: str = "",
        location: Optional[str] = None
    ) -> str:
        """
        Add a web search to memory.
        
        Args:
            query: The search query
            results: The search results data
            search_type: Type of search (web_search, news_search, etc.)
            tags: List of tags for categorization
            notes: Optional notes about the search
            location: Location context (uses default if not provided)
            
        Returns:
            entry_id: Unique ID of the stored entry
        """
        now = datetime.now(UTC)
        timestamp = now.isoformat()
        entry_id = f"trend_{int(now.timestamp())}_{uuid.uuid4().hex[:6]}"
        
        self.memory[entry_id] = {
            "id": entry_id,
            "timestamp": timestamp,
            "type": search_type,
            "query": query,
            "topic": None,
            "location": location or self.default_location,
            "data": results,
            "tags": tags or [],
            "notes": notes
        }
        
        self._write_memory(self.memory)
        return entry_id

    def add_trend(
        self,
        topic: str,
        trend_data: Dict[str, Any],
        tags: Optional[List[str]] = None,
        notes: str = "",
        location: Optional[str] = None
    ) -> str:
        """
        Add a trending topic to memory.
        
        Args:
            topic: The trending topic
            trend_data: The trend data/details
            tags: List of tags for categorization
            notes: Optional notes about the trend
            location: Location context (uses default if not provided)
            
        Returns:
            entry_id: Unique ID of the stored entry
        """
        now = datetime.now(UTC)
        timestamp = now.isoformat()
        entry_id = f"trend_{int(now.timestamp())}_{uuid.uuid4().hex[:6]}"
        
        self.memory[entry_id] = {
            "id": entry_id,
            "timestamp": timestamp,
            "type": "trending_topic",
            "query": None,
            "topic": topic,
            "location": location or self.default_location,
            "data": trend_data,
            "tags": tags or [],
            "notes": notes
        }
        
        self._write_memory(self.memory)
        return entry_id

    def get_recent(self, days: int = 7) -> List[Dict]:
        """Return entries from the last N days, sorted by timestamp (newest first)."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        results = [
            entry for entry in self.memory.values()
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff
        ]
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def search_history(self, query: str, days: int = 30) -> List[Dict]:
        """
        Find if we've searched for something similar before.
        
        Args:
            query: Search query to look for (case-insensitive partial match)
            days: Number of days to search back
            
        Returns:
            List of matching search entries
        """
        query_lower = query.lower()
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        results = []
        for entry in self.memory.values():
            # Only check search entries (not trending topics)
            if entry.get("query") is None:
                continue
                
            # Check timestamp
            if datetime.fromisoformat(entry["timestamp"]) < cutoff:
                continue
                
            # Check query match
            if query_lower in entry["query"].lower():
                results.append(entry)
        
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def search_trends(
        self,
        search_type: Optional[str] = None,
        days: int = 30,
        location: Optional[str] = None
    ) -> List[Dict]:
        """
        Filter entries by type, time range, and location.
        
        Args:
            search_type: Filter by entry type (web_search, trending_topic, etc.)
            days: Only include entries from last N days
            location: Filter by location (case-insensitive partial match)
            
        Returns:
            List of matching entries sorted by timestamp (newest first)
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        results = list(self.memory.values())
        
        # Filter by time
        results = [
            entry for entry in results
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff
        ]
        
        # Filter by type
        if search_type:
            results = [
                entry for entry in results
                if entry.get("type") == search_type
            ]
        
        # Filter by location
        if location:
            location_lower = location.lower()
            results = [
                entry for entry in results
                if entry.get("location") and location_lower in entry["location"].lower()
            ]
        
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def get_by_tag(self, tag: str) -> List[Dict]:
        """Return entries with a specific tag."""
        return [
            entry for entry in self.memory.values()
            if tag in entry.get("tags", [])
        ]

    def all_entries(self) -> List[Dict]:
        """Return all entries sorted by timestamp (newest first)."""
        return sorted(
            self.memory.values(),
            key=lambda x: x["timestamp"],
            reverse=True
        )

    def delete_entry(self, entry_id: str) -> bool:
        """Delete a specific entry by ID."""
        if entry_id in self.memory:
            del self.memory[entry_id]
            self._write_memory(self.memory)
            return True
        return False

    def prune_old(self, older_than_days: int = 90):
        """Remove entries older than specified days."""
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        
        ids_to_delete = [
            entry_id for entry_id, entry in self.memory.items()
            if datetime.fromisoformat(entry["timestamp"]) < cutoff
        ]
        
        for entry_id in ids_to_delete:
            del self.memory[entry_id]
        
        if ids_to_delete:
            self._write_memory(self.memory)
        
        return len(ids_to_delete)

    def clear_all(self):
        """Clear all entries (use with caution!)."""
        self.memory = {}
        self._write_memory({})


# Usage example:
# from src.cluas_mcp.common.trend_memory import TrendMemory
#
# memory = TrendMemory(location="Brooklyn")
#
# # Add a web search
# memory.add_search(
#     query="corvid intelligence research",
#     results={"items": [...], "total_results": 150},
#     search_type="web_search",
#     tags=["research", "morning"],
#     notes="Triggered by: user question about crow cognition"
# )
#
# # Add a trending topic
# memory.add_trend(
#     topic="AI safety regulations",
#     trend_data={"rank": 3, "volume": "high", "related": [...]},
#     tags=["tech", "policy"],
#     notes="Spotted on Twitter trends"
# )
#
# # Check search history
# previous = memory.search_history("corvid", days=30)
# print(f"Found {len(previous)} previous searches for 'corvid'")
#
# # Get recent entries
# recent = memory.get_recent(days=7)