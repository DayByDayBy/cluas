"""
TypedDict definitions for message formats used in Gradio app.
Provides type safety for chat messages and LLM communication.
"""
from typing import TypedDict, Literal, Optional


class ChatMessage(TypedDict, total=False):
    """Chat message format for Gradio UI."""
    role: Literal["user", "assistant"]
    content: str
    name: str  # Character name for assistant messages
    emoji: str  # Character emoji
    typing: bool  # True if message is a typing indicator
    streaming: bool  # True if message is currently streaming
    message_id: str  # Unique ID for message (for streaming optimization)


class LLMMessage(TypedDict):
    """Message format for LLM API calls."""
    role: Literal["user", "assistant", "system"]
    content: str


class ToolCallMessage(TypedDict):
    """Message format with tool calls."""
    role: Literal["assistant"]
    content: Optional[str]
    tool_calls: list[dict]

