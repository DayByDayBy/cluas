import pytest
import asyncio
from src.gradio.app import deliberate, CHARACTERS

@pytest.mark.asyncio
async def test_basic_deliberation():
    question = "How do crows solve problems creatively?"
    
    result = await deliberate(question, rounds=1)
    
    # basic checks
    assert result["question"] == question
    assert result["rounds"] == 1
    assert "phases" in result
    assert "cycle_summaries" in result
    assert "final_summary" in result
    assert result["final_summary"]["content"]

@pytest.mark.asyncio
async def test_multiple_rounds():
    question = "How do corvids communicate complex ideas?"
    
    result = await deliberate(question, rounds=2)
    
    assert len(result["cycle_summaries"]) == 2
    # check that each phase has entries
    for phase in ["thesis", "antithesis", "synthesis"]:
        assert phase in result["phases"]
        assert len(result["phases"][phase]) > 0

@pytest.mark.asyncio
async def test_summariser_options():
    question = "What is the impact of urbanization on crows?"
    
    # use a specific character as summariser
    for char_name, *_ in CHARACTERS:
        result = await deliberate(question, summariser=char_name)
        assert result["final_summary"]["by"] == char_name

@pytest.mark.asyncio
async def test_format_and_structure_options():
    question = "Can crows understand human gestures?"
    
    # test 'chat' format
    chat_result = await deliberate(question, format="chat", structure="nested")
    assert all("role" in entry and "content" in entry for entry in chat_result["history"])
    
    # test flat structure
    flat_result = await deliberate(question, format="llm", structure="flat")
    assert isinstance(flat_result["phases"], list)
    
@pytest.mark.asyncio
async def test_random_seed_reproducibility():
    question = "Do crows plan ahead?"
    
    r1 = await deliberate(question, rounds=1, seed=42)
    r2 = await deliberate(question, rounds=1, seed=42)
    
    # the character order should be identical with the same seed
    assert r1["character_order"] == r2["character_order"]
    # the final summary should also match
    assert r1["final_summary"]["content"] == r2["final_summary"]["content"]
