import json
from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Optional
from difflib import SequenceMatcher


class PaperMemory:
    """
    lightweight JSON-backed memory system for AI agents.
    Stores items with title, DOI, snippet, timestamps, and tags.
    """

    def __init__(
        self, 
        memory_file: Optional[Path] = None): 
               
        self.memory_file = Path(memory_file) if memory_file else Path.home() / ".cluas_mcp" / "paper_memory.json"
        self._ensure_data_dir()
        
        if not self.memory_file.exists():
            self._write_memory({})
        self.memory = self._read_memory()

    # --- internal file operations ---
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

    def _read_memory(self) -> Dict:
        with open(self.memory_file, "r") as f:
            return json.load(f)

    def _write_memory(self, data: Dict):
        with open(self.memory_file, "w") as f:
            json.dump(data, f, indent=2)

    # --- memory operations ---
    def add_item(
        self, 
        title: str,
        doi: Optional[str] = None,
        snippet: Optional[str] = None,
        mentioned_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        now = datetime.now(UTC).isoformat()
        key = title.lower()  # simple key by title
        if key in self.memory:
            # update last referenced timestamp
            self.memory[key]["last_referenced"] = now
        else:
            self.memory[key] = {
                "title": title,
                "doi": doi,
                "snippet": snippet,
                "first_mentioned": now,
                "last_referenced": now,
                "mentioned_by": mentioned_by,
                "tags": tags or []
            }
        self._write_memory(self.memory)

    def get_recent(self, days: int = 7) -> List[Dict]:
        """Return items mentioned in the last `days`."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        recent = [
            item for item in self.memory.values()
            if datetime.fromisoformat(item["last_referenced"]) >= cutoff
        ]
        return recent

    def get_by_tag(self, tag: str) -> List[Dict]:
        """Return items that include a specific tag."""
        return [item for item in self.memory.values() if tag in item.get("tags", [])]

    def search_title(self, query: str) -> List[Dict]:
        """Return items whose title contains the query string."""
        query_lower = query.lower()
        return [
            item for item in self.memory.values()
            if query_lower in item["title"].lower()
        ]

    def all_items(self) -> List[Dict]:
        """Return all items in memory."""
        return list(self.memory.values())

    def prune_long_term(self, older_than_days: int = 365):
        """Optionally prune memory items older than `older_than_days`."""
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        keys_to_delete = [
            k for k, v in self.memory.items()
            if datetime.fromisoformat(v["first_mentioned"]) < cutoff
        ]
        for k in keys_to_delete:
            del self.memory[k]
        if keys_to_delete:
            self._write_memory(self.memory)

    def search_title_scored(self, query: str) -> List[Dict]:
        """Return items with relevance scores"""
        query_lower = query.lower()
        results = []
        
        for item in self.memory.values():
            title_lower = item["title"].lower()
            
            similarity = SequenceMatcher(None, query_lower, title_lower).ratio()
            
            query_words = set(query_lower.split())
            title_words = set(title_lower.split())
            word_overlap = len(query_words & title_words) / len(query_words) if query_words else 0
            
            score = (similarity * 0.7) + (word_overlap * 0.3)
            
            if score > 0.2:
                result = item.copy()
                result['relevance_score'] = score
                results.append(result)
                
            
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results