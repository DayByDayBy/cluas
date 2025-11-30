import pytest
import asyncio
import logging
from src.gradio.app import deliberate, CHARACTERS
from src.characters.registry import REGISTRY
from src.gradio.types import BaseMessage, to_llm_history

# Enable debug logging for tests
logging.basicConfig(level=logging.DEBUG)

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

@pytest.mark.asyncio
async def test_character_registry_populated():
    """Test that character registry is properly populated"""
    print(f"Registry size: {len(REGISTRY)}")
    print(f"Registry keys: {list(REGISTRY.keys())}")
    
    # Registry should have characters
    assert len(REGISTRY) > 0, "Character registry is empty!"
    
    # Check expected characters exist
    expected_chars = ["corvus", "magpie", "raven", "crow"]
    for char_name in expected_chars:
        assert char_name in REGISTRY, f"Character {char_name} not in registry"
        char = REGISTRY[char_name]
        assert hasattr(char, 'name'), f"Character {char_name} missing name attribute"
        assert char.name, f"Character {char_name} has empty name"

@pytest.mark.asyncio
async def test_message_formatting_functions():
    """Test message formatting utilities"""
    # Test BaseMessage creation
    msg = BaseMessage(role="user", speaker="user", content="Hello world")
    assert msg.role == "user"
    assert msg.content == "Hello world"
    
    # Test to_llm_history conversion
    msgs = [msg, BaseMessage(role="assistant", speaker="corvus", content="Hi there")]
    llm_hist = to_llm_history(msgs)
    assert len(llm_hist) == 2
    assert llm_hist[0] == {"role": "user", "content": "Hello world"}
    assert llm_hist[1] == {"role": "assistant", "content": "Hi there"}

@pytest.mark.asyncio
async def test_deliberation_content_not_empty():
    """Test that deliberation produces actual content, not empty strings"""
    question = "What do crows think about humans?"
    
    result = await deliberate(question, rounds=1, format="llm", structure="flat")
    
    # Check that phases have actual content
    phases = result["phases"]
    assert isinstance(phases, list), "Phases should be a list in flat structure"
    
    # Each entry should have non-empty content
    for entry in phases:
        assert "content" in entry, f"Entry missing content: {entry}"
        content = entry["content"]
        assert content and content.strip(), f"Empty content in entry: {entry}"
        print(f"Phase {entry['phase']} by {entry['name']}: {content[:50]}...")
    
    # Final summary should not be empty
    final_summary = result["final_summary"]["content"]
    assert final_summary and final_summary.strip(), "Final summary is empty!"
    print(f"Final summary: {final_summary[:100]}...")

@pytest.mark.asyncio
async def test_deliberation_html_formatting():
    """Test that chat format produces proper HTML"""
    question = "How do birds solve puzzles?"
    
    result = await deliberate(question, rounds=1, format="chat", structure="nested")
    
    # History should be HTML string when format="chat"
    history = result["history"]
    assert isinstance(history, str), f"History should be string in chat format, got {type(history)}"
    assert "deliberation-container" in history, "Missing deliberation-container class"
    assert "delib-message" in history, "Missing delib-message class"
    assert "delib-content" in history, "Missing delib-content class"
    
    print(f"HTML output length: {len(history)} characters")
    print(f"HTML preview: {history[:200]}...")

@pytest.mark.asyncio
async def test_run_deliberation_and_export():
    """Test the export function that handles different formats"""
    from src.gradio.app import run_deliberation_and_export
    
    question = "How do birds navigate?"
    
    # Test export function
    display_html, tmp_path = await run_deliberation_and_export(
        question, rounds=1, summariser="moderator"
    )
    
    # Should return HTML and file path
    assert isinstance(display_html, str), "Display should be HTML string"
    assert tmp_path is not None, "Should create temporary file"
    assert "deliberation-container" in display_html, "Missing HTML in export output"
    
    print(f"Export HTML length: {len(display_html)} characters")
    print(f"Export file: {tmp_path}")
    
    # Clean up
    import os
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
