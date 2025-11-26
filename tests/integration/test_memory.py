import tempfile
from pathlib import Path
from src.cluas_mcp.common.observation_memory import ObservationMemory
from src.cluas_mcp.common.paper_memory import PaperMemory
from src.cluas_mcp.common.trend_memory import TrendMemory

def test_observation_memory(tmp_dir):
    mem_path = Path(tmp_dir) / "observations.json"
    memory = ObservationMemory(memory_file=str(mem_path))
    memory.add_observation("bird_sighting", "Tokyo", {"species": "Crow"})
    assert mem_path.exists()
    assert memory.get_recent()

def test_paper_memory(tmp_dir):
    mem_path = Path(tmp_dir) / "papers.json"
    memory = PaperMemory(memory_file=str(mem_path))
    memory.add_item("Test Paper")
    assert mem_path.exists()
    assert memory.get_recent()

def test_trend_memory(tmp_dir):
    memory = TrendMemory()
    entry_id = memory.add_trend("topic", {"data": True})
    assert entry_id

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        test_observation_memory(tmp)
        test_paper_memory(tmp)
        test_trend_memory(tmp)
    print("All memory tests passed.")