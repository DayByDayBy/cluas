import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from difflib import SequenceMatcher


class AgentMemory:
    """
    lightweight JSON-backed memory system for AI agents.
    Stores items with title, DOI, snippet, timestamps, and tags.
    """

    def __init__(self, memory_file: str = "src/data/memory.json"):
        self.memory_file = Path(memory_file)
        if not self.memory_file.exists():
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
    def add_item(
        self, 
        title: str,
        doi: Optional[str] = None,
        snippet: Optional[str] = None,
        mentioned_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        now = datetime.utcnow().isoformat()
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
        cutoff = datetime.utcnow() - timedelta(days=days)
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
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        keys_to_delete = [
            k for k, v in self.memory.items()
            if datetime.fromisoformat(v["first_mentioned"]) < cutoff
        ]
        for k in keys_to_delete:
            del self.memory[k]
        if keys_to_delete:
            self._write_memory(self.memory)

def search_titl_scored(self, query: str) -> List[Dict]:
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
        
        
    results.sort(key=lambda x: x['relevance_socre'], reverse=True)
    return results





# poss usage example:
    
# from src.cluas_mcp.common.memory import AgentMemory

# memory = AgentMemory()

# # adding a new paper
# memory.add_item(
#     title="Cognitive Ecology of Corvids",
#     doi="10.1234/example",
#     snippet="Corvids exhibit complex problem-solving abilities...",
#     mentioned_by="Corvus",
#     tags=["cognition", "tool_use"]
# )

# # retrieve recent items
# recent = memory.get_recent(days=14)
# print(recent)

# # search by tag
# cognition_items = memory.get_by_tag("cognition")

# # search by title
# search_results = memory.search_title("corvid")
