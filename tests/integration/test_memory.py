import pytest
from pathlib import Path
from src.cluas_mcp.common.observation_memory import ObservationMemory
from src.cluas_mcp.common.paper_memory import PaperMemory
from src.cluas_mcp.common.trend_memory import TrendMemory


def test_observation_memory(tmp_path):
    mem_path = tmp_path / "observations.json"
    memory = ObservationMemory(memory_file=str(mem_path))
    
    memory.add_observation("bird_sighting", "Tokyo", {"species": "Crow"})
    
    # file should exist
    assert mem_path.exists()
    
    # memory retrieval
    recent = memory.get_recent()
    assert recent
    assert recent[0]["type"] == "bird_sighting"
    assert recent[0]["location"] == "Tokyo"

def test_paper_memory(tmp_path):
    mem_path = tmp_path / "papers.json"
    memory = PaperMemory(memory_file=str(mem_path))
    
    memory.add_item("Test Paper")
    
    assert mem_path.exists()
    
    recent = memory.get_recent()
    assert recent
    assert recent[0]["title"] == "Test Paper"
    
    # clear and confirm empty
    memory.prune_long_term(older_than_days=0)
    assert len(memory.all_items()) == 0

def test_trend_memory(tmp_path):
    mem_path = tmp_path / "trends.json"
    memory = TrendMemory(memory_file=str(mem_path))
    
    entry_id = memory.add_trend("topic", {"data": True})
    assert entry_id
    
    retrieved = memory.get_recent()
    assert any(e["id"] == entry_id for e in retrieved)




