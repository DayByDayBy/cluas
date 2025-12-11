import pytest
from src.cluas_mcp.common import ObservationMemory, PaperMemory, TrendMemory


# ============================================================================
# ObservationMemory Tests
# ============================================================================

class TestObservationMemory:
    """Tests for ObservationMemory - bird sightings, weather, etc."""
    
    @pytest.fixture
    def memory(self, tmp_path):
        return ObservationMemory(memory_file=str(tmp_path / "obs.json"))
    
    def test_add_and_retrieve(self, memory):
        obs_id = memory.add_observation("bird_sighting", "Tokyo", {"species": "Crow"})
        
        assert obs_id.startswith("obs_")
        recent = memory.get_recent()
        assert len(recent) == 1
        assert recent[0]["type"] == "bird_sighting"
        assert recent[0]["data"]["species"] == "Crow"
    
    def test_add_with_full_metadata(self, memory):
        obs_id = memory.add_observation(
            obs_type="bird_sighting",
            location="Brooklyn, NY",
            data={"species": "American Crow", "count": 3},
            conditions={"weather": "Clear", "temperature": 18.5},
            tags=["morning", "urban"],
            notes="Spotted near park"
        )
        
        obs = memory.memory[obs_id]
        assert obs["conditions"]["weather"] == "Clear"
        assert "morning" in obs["tags"]
        assert obs["notes"] == "Spotted near park"
    
    def test_get_by_type(self, memory):
        memory.add_observation("bird_sighting", "Tokyo", {"species": "Crow"})
        memory.add_observation("weather", "Tokyo", {"temp": 20})
        memory.add_observation("bird_sighting", "Osaka", {"species": "Raven"})
        
        birds = memory.get_by_type("bird_sighting")
        assert len(birds) == 2
        assert all(b["type"] == "bird_sighting" for b in birds)
    
    def test_get_by_location_case_insensitive(self, memory):
        memory.add_observation("bird_sighting", "Tokyo, Japan", {"species": "Crow"})
        memory.add_observation("bird_sighting", "tokyo station", {"species": "Magpie"})
        
        results = memory.get_by_location("TOKYO")
        assert len(results) == 2
    
    def test_get_by_tag(self, memory):
        memory.add_observation("bird_sighting", "NYC", {"species": "Crow"}, tags=["urban", "morning"])
        memory.add_observation("bird_sighting", "NYC", {"species": "Raven"}, tags=["urban"])
        memory.add_observation("bird_sighting", "NYC", {"species": "Jay"}, tags=["morning"])
        
        urban = memory.get_by_tag("urban")
        assert len(urban) == 2
    
    def test_search_observations_combined(self, memory):
        memory.add_observation("bird_sighting", "Tokyo", {"species": "Crow"}, tags=["urban"])
        memory.add_observation("bird_sighting", "Osaka", {"species": "Raven"}, tags=["urban"])
        memory.add_observation("weather", "Tokyo", {"temp": 20}, tags=["urban"])
        
        results = memory.search_observations(obs_type="bird_sighting", location="Tokyo", tags=["urban"])
        assert len(results) == 1
        assert results[0]["data"]["species"] == "Crow"
    
    def test_delete_observation(self, memory):
        obs_id = memory.add_observation("bird_sighting", "Tokyo", {"species": "Crow"})
        assert len(memory.all_observations()) == 1
        
        deleted = memory.delete_observation(obs_id)
        assert deleted is True
        assert len(memory.all_observations()) == 0
        
        # deleting non-existent returns False
        assert memory.delete_observation("fake_id") is False
    
    def test_clear_all(self, memory):
        memory.add_observation("bird_sighting", "Tokyo", {"species": "Crow"})
        memory.add_observation("weather", "Tokyo", {"temp": 20})
        
        memory.clear_all()
        assert len(memory.all_observations()) == 0
    
    def test_default_location_filtering(self, tmp_path):
        memory = ObservationMemory(location="Tokyo", memory_file=str(tmp_path / "obs.json"))
        memory.add_observation("bird_sighting", "Tokyo", {"species": "Crow"})
        memory.add_observation("bird_sighting", "Osaka", {"species": "Raven"})
        
        # get_recent with default location should filter
        recent = memory.get_recent()
        assert len(recent) == 1
        assert recent[0]["location"] == "Tokyo"


# ============================================================================
# PaperMemory Tests
# ============================================================================

class TestPaperMemory:
    """Tests for PaperMemory - academic paper tracking."""
    
    @pytest.fixture
    def memory(self, tmp_path):
        return PaperMemory(memory_file=str(tmp_path / "papers.json"))
    
    def test_add_and_retrieve(self, memory):
        memory.add_item("Corvid Cognition Study")
        
        recent = memory.get_recent()
        assert len(recent) == 1
        assert recent[0]["title"] == "Corvid Cognition Study"
    
    def test_add_with_full_metadata(self, memory):
        memory.add_item(
            title="Tool Use in New Caledonian Crows",
            doi="10.1234/crows",
            snippet="This study examines tool manufacturing...",
            mentioned_by="Corvus",
            tags=["tool_use", "cognition"]
        )
        
        items = memory.all_items()
        assert items[0]["doi"] == "10.1234/crows"
        assert items[0]["mentioned_by"] == "Corvus"
        assert "tool_use" in items[0]["tags"]
    
    def test_duplicate_updates_timestamp(self, memory):
        memory.add_item("Same Paper")
        first_ref = memory.all_items()[0]["last_referenced"]
        
        # add same paper again
        memory.add_item("Same Paper")
        
        # should still be one item
        assert len(memory.all_items()) == 1
        # timestamp should be updated
        assert memory.all_items()[0]["last_referenced"] >= first_ref
    
    def test_search_title(self, memory):
        memory.add_item("Corvid Intelligence")
        memory.add_item("Crow Problem Solving")
        memory.add_item("Unrelated Paper")
        
        results = memory.search_title("corv")
        assert len(results) == 1
        assert "Corvid" in results[0]["title"]
    
    def test_search_title_scored(self, memory):
        memory.add_item("Corvid Tool Use")
        memory.add_item("Tool Manufacturing in Birds")
        memory.add_item("Unrelated Topic")
        
        results = memory.search_title_scored("corvid tool")
        assert len(results) >= 1
        # best match should be first
        assert "Corvid" in results[0]["title"]
        assert "relevance_score" in results[0]
    
    def test_get_by_tag(self, memory):
        memory.add_item("Paper A", tags=["cognition", "tool_use"])
        memory.add_item("Paper B", tags=["cognition"])
        memory.add_item("Paper C", tags=["behavior"])
        
        cognition_papers = memory.get_by_tag("cognition")
        assert len(cognition_papers) == 2


# ============================================================================
# TrendMemory Tests
# ============================================================================

class TestTrendMemory:
    """Tests for TrendMemory - web searches and trending topics."""
    
    @pytest.fixture
    def memory(self, tmp_path):
        return TrendMemory(memory_file=str(tmp_path / "trends.json"))
    
    def test_add_search(self, memory):
        entry_id = memory.add_search(
            query="corvid intelligence",
            results={"items": [{"title": "Result 1"}], "total": 100}
        )
        
        assert entry_id.startswith("trend_")
        recent = memory.get_recent()
        assert len(recent) == 1
        assert recent[0]["query"] == "corvid intelligence"
        assert recent[0]["type"] == "web_search"
    
    def test_add_trend(self, memory):
        entry_id = memory.add_trend(
            topic="AI Safety",
            trend_data={"rank": 3, "volume": "high"}
        )
        
        recent = memory.get_recent()
        assert recent[0]["topic"] == "AI Safety"
        assert recent[0]["type"] == "trending_topic"
    
    def test_search_history(self, memory):
        memory.add_search("corvid behavior", {"items": []})
        memory.add_search("crow intelligence", {"items": []})
        memory.add_search("unrelated query", {"items": []})
        
        # partial match
        results = memory.search_history("corv")
        assert len(results) == 1
        assert "corvid" in results[0]["query"]
    
    def test_search_trends_by_type(self, memory):
        memory.add_search("query1", {"items": []})
        memory.add_trend("topic1", {"data": True})
        memory.add_trend("topic2", {"data": True})
        
        trends = memory.search_trends(search_type="trending_topic")
        assert len(trends) == 2
        assert all(t["type"] == "trending_topic" for t in trends)
    
    def test_search_trends_by_location(self, tmp_path):
        memory = TrendMemory(location="Brooklyn", memory_file=str(tmp_path / "trends.json"))
        
        memory.add_search("query1", {"items": []})  # uses default location
        memory.add_search("query2", {"items": []}, location="Manhattan")
        
        brooklyn = memory.search_trends(location="brooklyn")
        assert len(brooklyn) == 1
    
    def test_get_by_tag(self, memory):
        memory.add_search("query1", {"items": []}, tags=["research"])
        memory.add_trend("topic1", {"data": True}, tags=["research", "tech"])
        memory.add_trend("topic2", {"data": True}, tags=["news"])
        
        research = memory.get_by_tag("research")
        assert len(research) == 2
    
    def test_delete_entry(self, memory):
        entry_id = memory.add_trend("topic", {"data": True})
        assert len(memory.all_entries()) == 1
        
        deleted = memory.delete_entry(entry_id)
        assert deleted is True
        assert len(memory.all_entries()) == 0
    
    def test_clear_all(self, memory):
        memory.add_search("q1", {})
        memory.add_trend("t1", {})
        
        memory.clear_all()
        assert len(memory.all_entries()) == 0