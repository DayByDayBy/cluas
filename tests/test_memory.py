import pytest
from src.characters.corvus import Corvus

@pytest.fixture
def corvus():
    c = Corvus()
    c.clear_memory()  # start w clean slate
    yield c
    c.clear_memory()  # cleean up after test

def test_memory_persistence(corvus):
    # add some papers (memories)
    corvus.memory.add_item(
        title="Test Paper",
        doi="10.1234/test",
        snippet="Test abstract",
        mentioned_by="Corvus"
    )
    
    # verify it's actually been saved
    papers = corvus.memory.all_items()
    assert len(papers) == 1
    
    # cleaer, verify empty
    corvus.clear_memory()
    assert len(corvus.memory.all_items()) == 0