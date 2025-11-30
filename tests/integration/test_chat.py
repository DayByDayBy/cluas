import pytest
import asyncio
import logging
from src.gradio.app import chat_fn, parse_mentions
from src.characters.registry import REGISTRY
from src.gradio.types import BaseMessage, from_gradio_format, to_gradio_history


@pytest.mark.asyncio
async def test_basic_chat_function(caplog):
    """Test basic chat functionality without mentions"""
    with caplog.at_level(logging.DEBUG):
        message = "Hello, what do you think about crows?"
        
        # Start with empty history
        history = []
        
        # Call chat function
        result = []
        async for update in chat_fn(message, history.copy()):
            result.append(update)
        
        # Should get at least one update
        assert len(result) > 0, "Chat should return updates"
        
        # Final result should have history entries
        final_history = result[-1]
        assert isinstance(final_history, list), "Final result should be history list"
        assert len(final_history) > 0, "History should have entries"
        
        print(f"Chat returned {len(final_history)} history entries")
        for i, entry in enumerate(final_history):
            print(f"Entry {i}: {entry.get('role', 'unknown')} - {entry.get('content', {})[:50]}...")

@pytest.mark.asyncio
async def test_single_character_mention(caplog):
    """Test @mention system with single character"""
    with caplog.at_level(logging.DEBUG):
        # Ensure registry has characters
        assert len(REGISTRY) > 0, "Registry should have characters for mention test"
        
        # Get first character name
        char_name = list(REGISTRY.keys())[0]
        
        message = f"@{char_name} what is your opinion on urban adaptation?"
        history = []
        
        result = []
        async for update in chat_fn(message, history.copy()):
            result.append(update)
        
        final_history = result[-1]
        
        # Should have user message + character response
        assert len(final_history) >= 2, "Should have user message and character response"
        
        # Check user message is preserved
        user_entry = final_history[0]
        assert user_entry["role"] == "user", "First entry should be user message"
        assert message in user_entry["content"][0]["text"], "User message should contain mention"
        
        print(f"Mention test with @{char_name}: {len(final_history)} entries")

@pytest.mark.asyncio
async def test_multiple_character_mentions(caplog):
    """Test @mention system with multiple characters"""
    with caplog.at_level(logging.DEBUG):
        if len(REGISTRY) < 2:
            pytest.skip("Need at least 2 characters for multiple mention test")
        
        # Get first two character names
        char_names = list(REGISTRY.keys())[:2]
        mentions = " ".join([f"@{name}" for name in char_names])
        message = f"{mentions} what do you all think about tool use?"
        
        history = []
        result = []
        async for update in chat_fn(message, history.copy()):
            result.append(update)
        
        final_history = result[-1]
        
        # Should have user + responses from mentioned characters
        expected_entries = 1 + len(char_names)  # user + each mentioned character
        assert len(final_history) >= expected_entries, f"Should have at least {expected_entries} entries"
        
        print(f"Multiple mentions test: {char_names} -> {len(final_history)} entries")

@pytest.mark.asyncio
async def test_no_mentions_all_characters(caplog):
    """Test that without mentions, all characters respond"""
    with caplog.at_level(logging.DEBUG):
        message = "Tell me about your perspective on corvid intelligence"
        history = []
        
        result = []
        async for update in chat_fn(message, history.copy()):
            result.append(update)
        
        final_history = result[-1]
        
        # Should have user + all character responses
        expected_entries = 1 + len(REGISTRY)  # user + all characters
        assert len(final_history) >= expected_entries, f"Should have at least {expected_entries} entries for all characters"
        
        print(f"No mentions test: all {len(REGISTRY)} characters -> {len(final_history)} entries")

@pytest.mark.asyncio
async def test_invalid_mention_fallback(caplog):
    """Test @mention with non-existent character"""
    with caplog.at_level(logging.DEBUG):
        message = "@nonexistent_character what do you think?"
        history = []
        
        result = []
        async for update in chat_fn(message, history.copy()):
            result.append(update)
        
        final_history = result[-1]
        
        # Should still work (invalid mentions should be ignored)
        assert len(final_history) >= 1, "Should handle invalid mentions gracefully"
        
        print(f"Invalid mention test: {len(final_history)} entries (should handle gracefully)")

def test_parse_mentions_function():
    """Test the parse_mentions utility function directly"""
    # Test single mention
    message1 = "@corvus what do you think?"
    mentions1 = parse_mentions(message1)
    assert mentions1 == ["corvus"], f"Single mention failed: {mentions1}"
    
    # Test multiple mentions
    message2 = "@corvus and @raven, what are your opinions?"
    mentions2 = parse_mentions(message2)
    assert set(mentions2) == {"corvus", "raven"}, f"Multiple mentions failed: {mentions2}"
    
    # Test no mentions
    message3 = "what does everyone think?"
    mentions3 = parse_mentions(message3)
    assert mentions3 is None, f"No mentions should return None, got: {mentions3}"
    
    # Test mention with punctuation
    message4 = "@corvus, what about tool use? @raven?"
    mentions4 = parse_mentions(message4)
    assert set(mentions4) == {"corvus", "raven"}, f"Mentions with punctuation failed: {mentions4}"
    
    print("Parse mentions function tests passed")

def test_message_formatting_roundtrip():
    """Test message formatting utilities for chat"""
    # Test Gradio format roundtrip
    gradio_msg = {
        "role": "user", 
        "content": [{"type": "text", "text": "@corvus hello there"}]
    }
    
    # Parse back to BaseMessage
    parsed = from_gradio_format(gradio_msg)
    assert parsed.role == "user", "Role should be preserved"
    assert "@corvus hello there" in parsed.content, "Content should be preserved"
    assert parsed.speaker == "user", "Speaker should be user"
    
    # Convert back to Gradio format
    back_to_gradio = to_gradio_history([parsed])
    assert len(back_to_gradio) == 1, "Should have one message"
    assert back_to_gradio[0]["role"] == "user", "Role should match"
    
    print("Message formatting roundtrip tests passed")

@pytest.mark.asyncio
async def test_chat_with_history_context(caplog):
    """Test chat with previous conversation history"""
    with caplog.at_level(logging.DEBUG):
        # Create some history
        history = [
            {
                "role": "user", 
                "content": [{"type": "text", "text": "What do crows think about puzzles?"}]
            },
            {
                "role": "assistant", 
                "content": [{"type": "text", "text": "🐦‍⬛ Corvus: Crows show remarkable problem-solving abilities..."}]
            }
        ]
        
        # Follow-up message
        follow_up = "Can you give me a specific example?"
        
        result = []
        async for update in chat_fn(follow_up, history.copy()):
            result.append(update)
        
        final_history = result[-1]
        
        # Should have previous history + new messages
        assert len(final_history) > len(history), "Should have new messages added to history"
        
        print(f"Chat with history test: {len(history)} -> {len(final_history)} entries")