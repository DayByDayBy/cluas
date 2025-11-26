import pytest
from src.gradio.app import deliberate, CHARACTERS

@pytest.mark.asyncio
async def test_single_round_moderator_summary():
    result = await deliberate(
        question="What's the best way to help urban crows?",
        rounds=1,
        summariser="moderator",
        format="chat",
        structure="nested",
        seed=42
    )

    # basic checks
    assert "phases" in result
    assert all(phase in result["phases"] for phase in ("thesis", "antithesis", "synthesis"))
    assert "final_summary" in result
    assert isinstance(result["final_summary"]["content"], str)
    assert len(result["final_summary"]["content"]) > 0

@pytest.mark.asyncio
async def test_multiple_rounds_consistency():
    # fixed seed should produce consistent character order
    result1 = await deliberate("Question?", rounds=2, seed=123)
    result2 = await deliberate("Question?", rounds=2, seed=123)
    assert result1["character_order"] == result2["character_order"]

@pytest.mark.asyncio
async def test_summariser_character_choice():
    for name, _, _, _, _ in CHARACTERS:
        result = await deliberate(
            question="Test summariser by character",
            rounds=1,
            summariser=name,
            format="llm",
            structure="flat",
            seed=99
        )
        # ensure final_summary is generated and attributed correctly
        assert result["final_summary"]["by"] == name
        assert len(result["final_summary"]["content"]) > 0

@pytest.mark.asyncio
async def test_output_formats():
    for fmt in ["chat", "llm"]:
        result = await deliberate(
            question="Check output formats",
            rounds=1,
            summariser="moderator",
            format=fmt,
            structure="nested",
        )
        if fmt == "chat":
            # should be list of dicts with 'role' and 'content'
            first_entry = result["history"][0]
            assert "role" in first_entry and "content" in first_entry
        else:
            # LLM format should be plain strings
            assert all(isinstance(item, str) for item in result["history"])
